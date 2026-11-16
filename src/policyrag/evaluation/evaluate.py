"""Evaluation harness + regression gate.

    python -m policyrag.evaluation.evaluate --name baseline --gate
    python -m policyrag.evaluation.evaluate --name no-rerank --set rerank=false --limit 60 --no-judge --gate
    python -m policyrag.evaluation.evaluate --name baseline --update-baseline

Exit code 1 if the gate fails, so CI can block a merge.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from policyrag.config import PROJECT_ROOT, get_settings
from policyrag.evaluation.golden_set import GoldenCase, load_golden, stratified_sample
from policyrag.generation.prompts import ABSTAIN_TEXT
from policyrag.textnorm import contains_all_groups, contains_any

GATE_FILE = PROJECT_ROOT / "config" / "eval_gate.yaml"


# ---------------------------------------------------------------- per-case scoring
_COMPARE_EXPECTED = re.compile(r"^(?P<winner>.+?) \((?P<a>[^:]+): [^;]+; (?P<b>[^:]+): [^)]+\)\.?$")
_OPPOSITE = {"lower": "higher", "higher": "lower", "shorter": "longer", "longer": "shorter",
             "faster": "slower", "slower": "faster", "fewer": "more", "more": "fewer", "less": "more"}
_COMPARATIVE = re.compile(r"\b(" + "|".join(_OPPOSITE) + r")\b", re.I)
# sentence AND clause boundaries: the conclusion often follows ", so" / "; therefore" in one sentence
_SENTENCE = re.compile(r"(?<=[.!?])\s+|,\s*(?:so|thus|therefore|which means)\b|;\s*|\b(?:therefore|thus),?\s", re.I)


def comparison_winner_ok(answer: str, expected: str, question: str = "") -> bool:
    """A comparison is only correct if the answer's conclusion picks the right winner.

    Finds the last sentence containing a comparative ("X has the shorter ...", "Therefore Y is higher"),
    takes the first product named in it as the subject, and flips the pick when the comparative is the
    opposite of the one asked ("Term 30 is faster" answers "which is slower?" with the other product).
    No conclusion, or calling the values equal, is wrong (golden values always differ).
    """
    m = _COMPARE_EXPECTED.match(expected)
    if not m:
        return True
    names = (m["a"], m["b"])
    asked_m = _COMPARATIVE.search(question)
    asked = asked_m.group(1).lower() if asked_m else None
    for sent in reversed(_SENTENCE.split(answer.strip())):
        cm = _COMPARATIVE.search(sent)
        low = sent.lower()
        pos = {n: low.find(n.lower()) for n in names}
        present = sorted((p, n) for n, p in pos.items() if p >= 0)
        if not cm or not present:
            continue
        if re.search(r"\b(both|same|equal|identical)\b", low):
            return False
        subject = present[0][1]
        word = cm.group(1).lower()
        if asked and word == _OPPOSITE.get(asked):
            pick = names[1] if subject == names[0] else names[0]
        else:
            pick = subject
        return pick == m["winner"]
    return False


def chunk_is_relevant(hit: dict, case: GoldenCase) -> bool:
    return any(hit["doc_id"] in f.doc_ids and contains_any(hit["text"], f.match) for f in case.facts)


def score_case(case: GoldenCase, out: dict) -> dict:
    hits = out["retrieved"]
    answer = out["answer"]
    abstained = (not out["answerable"]) or answer.strip().startswith(ABSTAIN_TEXT[:20])
    row: dict = {"id": case.id, "type": case.type, "question": case.question, "expected": case.expected_answer,
                 "answer": answer, "abstained": abstained, "status": out["status"],
                 "review_reasons": out["review_reasons"], "route": out["route"]["name"], "model": out["route"]["model"],
                 "fallback_used": out["route"]["fallback_used"], "confidence": out["confidence"]["final"],
                 "latency_ms": out["latency_ms"]["total"], "llm_ms": out["latency_ms"].get("llm", 0.0),
                 "retrieval_ms": out["latency_ms"].get("retrieval", 0.0),
                 "input_tokens": out["usage"]["input_tokens"], "output_tokens": out["usage"]["output_tokens"],
                 "cost_usd": out["usage"]["cost_usd_estimate"],
                 "format_valid_first_try": out["format"]["valid_first_try"], "format_valid": out["format"]["valid"],
                 "format_coerced": bool(out["format"]["coerced"]), "format_repaired": out["format"]["repaired"],
                 "retrieved_ids": [h["chunk_id"] for h in hits], "cited_ids": [s["chunk_id"] for s in out["sources"]],
                 "invalid_citations": out["invalid_citations"]}

    row["internal_leak"] = ("internal" not in case.allowed_confidentiality and
                            any(h["chunk_id"].startswith("internal-") for h in hits))

    if case.answerable:
        rel = [chunk_is_relevant(h, case) for h in hits]
        covered = [any(h["doc_id"] in f.doc_ids and contains_any(h["text"], f.match) for h in hits) for f in case.facts]
        row["hit"] = any(rel)
        row["context_recall"] = sum(covered) / len(covered) if covered else 0.0
        first = next((i for i, r in enumerate(rel) if r), None)
        row["mrr"] = 0.0 if first is None else 1.0 / (first + 1)
        # RAGAS-style context precision: mean precision@k over the ranks that hold a relevant chunk
        prec, n_rel = [], 0
        for k, r in enumerate(rel, start=1):
            if r:
                n_rel += 1
                prec.append(n_rel / k)
        row["context_precision"] = float(np.mean(prec)) if prec else 0.0
        row["correct"] = (not abstained) and contains_all_groups(answer, case.must_contain)
        if case.type == "comparison":
            row["correct"] = row["correct"] and comparison_winner_ok(answer, case.expected_answer, case.question)
        cited = [h for h in hits if h["chunk_id"] in row["cited_ids"]]
        row["citation_relevant"] = (not abstained) and any(chunk_is_relevant(h, case) for h in cited)
    else:
        row["correct"] = abstained
    row["citation_valid"] = abstained or (bool(row["cited_ids"]) and not row["invalid_citations"])
    return row


# ---------------------------------------------------------------- aggregation
def _mean(rows, key, pred=lambda r: True):
    vals = [r[key] for r in rows if pred(r) and r.get(key) is not None]
    return round(float(np.mean(vals)), 4) if vals else None


def summarize(rows: list[dict]) -> dict:
    ans = [r for r in rows if "hit" in r]
    unans = [r for r in rows if "hit" not in r]
    errors = [r for r in rows if not r["correct"]]
    auto = [r for r in rows if r["status"] == "answered"]
    lat = np.array([r["latency_ms"] for r in rows])
    by_type = {}
    for t in sorted({r["type"] for r in rows}):
        g = [r for r in rows if r["type"] == t]
        by_type[t] = {"n": len(g), "accuracy": _mean(g, "correct")}
    routes = {}
    for name in sorted({r["route"] for r in rows}):
        g = [r for r in rows if r["route"] == name]
        routes[name] = {"share": round(len(g) / len(rows), 4), "accuracy": _mean(g, "correct"),
                        "latency_ms_p50": round(float(np.median([r["latency_ms"] for r in g])), 1),
                        "cost_usd_mean": _mean(g, "cost_usd")}
    cost = float(np.mean([r["cost_usd"] for r in rows]))
    return {
        "n": len(rows),
        "answer_accuracy": _mean(rows, "correct"),
        "accuracy_answerable": _mean(ans, "correct"),
        "abstention_accuracy": _mean(unans, "correct"),
        "false_abstention_rate": _mean(ans, "abstained"),
        "hallucination_rate": round(1 - _mean(unans, "correct"), 4) if unans else None,
        "by_type": by_type,
        "retrieval": {"hit_rate": _mean(ans, "hit"), "context_recall": _mean(ans, "context_recall"),
                      "mrr": _mean(ans, "mrr"), "context_precision": _mean(ans, "context_precision")},
        "faithfulness": _mean(rows, "faithfulness"),
        "answer_relevancy": _mean(rows, "answer_relevancy"),
        "format": {"valid_rate": _mean(rows, "format_valid"), "valid_first_try_rate": _mean(rows, "format_valid_first_try"),
                   "coerced_rate": _mean(rows, "format_coerced"), "repaired_rate": _mean(rows, "format_repaired")},
        "citations": {"valid_rate": _mean(rows, "citation_valid"), "relevant_rate": _mean(ans, "citation_relevant",
                                                                                       lambda r: not r["abstained"])},
        "review": {"flagged_rate": round(1 - len(auto) / len(rows), 4),
                   "auto_answer_accuracy": _mean(auto, "correct"),
                   "error_recall": round(sum(r["status"] == "needs_review" for r in errors) / len(errors), 4) if errors else 1.0},
        "routing": routes,
        "fallback_rate": _mean(rows, "fallback_used"),
        "latency_ms_p50": round(float(np.percentile(lat, 50)), 1),
        "latency_ms_p95": round(float(np.percentile(lat, 95)), 1),
        "llm_ms_p50": round(float(np.median([r["llm_ms"] for r in rows])), 1),
        "retrieval_ms_p50": round(float(np.median([r["retrieval_ms"] for r in rows])), 1),
        "tokens_in_mean": round(float(np.mean([r["input_tokens"] for r in rows])), 1),
        "tokens_out_mean": round(float(np.mean([r["output_tokens"] for r in rows])), 1),
        "cost_per_query_usd": round(cost, 8),
        "cost_per_1k_queries_usd": round(cost * 1000, 4),
        "internal_leaks": int(sum(r["internal_leak"] for r in rows)),
    }


# ---------------------------------------------------------------- gate
def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


def run_gate(summary: dict, baseline: dict | None, gate: dict) -> tuple[bool, list[dict]]:
    cur = flatten(summary)
    base = flatten(baseline) if baseline else {}
    checks = []

    def add(metric, kind, ok, value, limit):
        checks.append({"metric": metric, "check": kind, "value": value, "limit": limit, "pass": bool(ok)})

    for m, floor in (gate.get("floors") or {}).items():
        v = cur.get(m)
        add(m, ">= floor", v is not None and v >= floor, v, floor)
    for m, ceil in (gate.get("ceilings") or {}).items():
        v = cur.get(m)
        add(m, "<= ceiling", v is not None and v <= ceil, v, ceil)
    if base:
        for m, drop in (gate.get("max_drop") or {}).items():
            v, b = cur.get(m), base.get(m)
            if v is None or b is None:
                continue
            add(m, f"drop <= {drop} vs baseline", v >= b - drop, v, round(b - drop, 4))
        for m, ratio in (gate.get("max_increase_ratio") or {}).items():
            v, b = cur.get(m), base.get(m)
            if v is None or not b:
                continue
            add(m, f"<= {ratio}x baseline", v <= b * ratio, v, round(b * ratio, 4))
    return all(c["pass"] for c in checks), checks


# ---------------------------------------------------------------- runner
def coerce_value(v: str):
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def write_markdown(path: Path, report: dict) -> None:
    s = report["summary"]
    lines = [f"# Eval report: {report['name']}", "", f"- run at: {report['run_at']}",
             f"- cases: {s['n']}  |  judge: {report['judge']}  |  overrides: `{report['overrides']}`",
             f"- models: default `{report['models']['default']}`, small `{report['models']['small']}`, "
             f"judge `{report['models']['judge']}`", "",
             "| metric | value |", "|---|---|"]
    for k, v in flatten(s).items():
        lines.append(f"| {k} | {v} |")
    if report.get("gate"):
        g = report["gate"]
        lines += ["", f"## Gate: {'PASS' if g['passed'] else 'FAIL'}", "", "| metric | check | value | limit | pass |",
                  "|---|---|---|---|---|"]
        lines += [f"| {c['metric']} | {c['check']} | {c['value']} | {c['limit']} | {'✅' if c['pass'] else '❌'} |"
                  for c in g["checks"]]
    fails = [r for r in report["rows"] if not r["correct"]][:40]
    if fails:
        lines += ["", "## Incorrect cases", "", "| id | type | question | expected | got | status |", "|---|---|---|---|---|---|"]
        for r in fails:
            esc = lambda x: str(x).replace("|", "\\|").replace("\n", " ")[:160]  # noqa: E731
            lines.append(f"| {r['id']} | {r['type']} | {esc(r['question'])} | {esc(r['expected'])} | "
                         f"{esc(r['answer'])} | {r['status']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="run")
    ap.add_argument("--limit", type=int, default=0, help="stratified subset size (0 = all)")
    ap.add_argument("--types", default="", help="comma-separated case types to include")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a Settings field")
    ap.add_argument("--force-route", choices=["simple", "complex"], default=None)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args(argv)

    s = get_settings()
    overrides = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        if not hasattr(s, k):
            raise SystemExit(f"unknown setting {k!r}")
        overrides[k] = coerce_value(v)
        setattr(s, k, overrides[k])
    s.cache_enabled = False  # never let the cache leak answers between eval cases

    from policyrag.evaluation.judge import Judge
    from policyrag.generation.generator import AnswerService
    from policyrag.generation.prompts import format_context
    from policyrag.generation.review_queue import ReviewQueue
    from policyrag.monitoring.metrics import QueryLog
    from policyrag.retrieval.retriever import Filters, Retriever

    s.reports_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = s.reports_dir / "_eval_state"
    eval_dir.mkdir(exist_ok=True)
    retriever = Retriever(s.index_dir, s)
    svc = AnswerService(retriever=retriever, review=ReviewQueue(eval_dir / f"review_{args.name}.sqlite"),
                        cache=None, log=QueryLog(eval_dir / f"queries_{args.name}.jsonl"))
    judge = None if args.no_judge else Judge()

    cases = load_golden()
    if args.types:
        wanted = set(args.types.split(","))
        cases = [c for c in cases if c.type in wanted]
    if args.limit:
        cases = stratified_sample(cases, args.limit)

    svc.answer("warm-up: what is the late payment fee?", use_cache=False, enqueue_review=False)  # not scored

    rows = []
    t0 = time.perf_counter()
    for i, case in enumerate(cases, 1):
        out = svc.answer(case.question, Filters(allowed_confidentiality=tuple(case.allowed_confidentiality)),
                         use_cache=False, force_route=args.force_route)
        row = score_case(case, out)
        if judge and not row["abstained"]:
            ctx = format_context([_HitView(h) for h in out["retrieved"]], {})
            row["faithfulness"], row["claims"] = judge.faithfulness(ctx, out["answer"])
            row["answer_relevancy"] = judge.answer_relevancy(case.question, out["answer"])
        rows.append(row)
        mark = "ok " if row["correct"] else "BAD"
        print(f"[{i:3d}/{len(cases)}] {mark} {case.type:<12} {row['route']:<7} {row['latency_ms']:>8.0f}ms  {case.question[:70]}",
              flush=True)

    summary = summarize(rows)
    report = {
        "name": args.name, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overrides": overrides, "judge": judge is not None, "force_route": args.force_route,
        "models": {"default": s.llm_default, "small": s.llm_small, "judge": s.judge_model,
                   "embedding": s.embedding_model, "reranker": s.reranker_model},
        "index": retriever.manifest, "wall_seconds": round(time.perf_counter() - t0, 1),
        "judge_tokens": judge.tokens if judge else None, "summary": summary, "rows": rows,
    }

    baseline_path = s.reports_dir / "baseline.json"
    passed = True
    if args.gate:
        gate_cfg = yaml.safe_load(GATE_FILE.read_text(encoding="utf-8"))
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))["summary"] if baseline_path.exists() else None
        passed, checks = run_gate(summary, baseline, gate_cfg)
        report["gate"] = {"passed": passed, "checks": checks, "baseline": "baseline.json" if baseline else None}

    out_json = s.reports_dir / f"eval_{args.name}.json"
    out_json.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    write_markdown(s.reports_dir / f"eval_{args.name}.md", report)
    if args.update_baseline:
        baseline_path.write_text(json.dumps({"from": out_json.name, "summary": summary}, indent=2), encoding="utf-8")

    keys = ["answer_accuracy", "abstention_accuracy", "hallucination_rate", "retrieval.hit_rate",
            "retrieval.context_recall", "faithfulness", "answer_relevancy", "format.valid_rate",
            "review.auto_answer_accuracy", "review.error_recall", "latency_ms_p50", "latency_ms_p95",
            "cost_per_1k_queries_usd", "internal_leaks"]
    flat = flatten(summary)
    print("\n" + "\n".join(f"  {k:<30} {flat.get(k)}" for k in keys))
    if args.gate:
        print(f"\nGATE: {'PASS' if passed else 'FAIL'}")
        for c in report["gate"]["checks"]:
            if not c["pass"]:
                print(f"  FAIL {c['metric']}: {c['value']} ({c['check']}, limit {c['limit']})")
    print(f"\nreport: {out_json}")
    return 0 if passed else 1


class _HitView:
    """Adapter so format_context can render the retrieved dicts from a result payload."""

    def __init__(self, d: dict):
        self.chunk = {"chunk_id": d["chunk_id"], "title": d["title"], "section": d["section"],
                      "doc_type": d["doc_type"], "last_updated": d["last_updated"], "text": d["text"],
                      "doc_id": d["doc_id"]}


if __name__ == "__main__":
    sys.exit(main())
