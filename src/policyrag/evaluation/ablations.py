"""Ablation suite: disable one component at a time and run the gate against the baseline.

    python -m policyrag.evaluation.ablations --limit 90

Each variant runs in its own subprocess (clean settings), and the results are collected
into reports/ablations.md. This is the evidence for "what is each component worth" and
"does the gate actually catch regressions".
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from policyrag.config import PROJECT_ROOT, get_settings
from policyrag.evaluation.evaluate import flatten

VARIANTS: list[tuple[str, list[str], str]] = [
    ("full", [], "everything on (reference)"),
    ("no-rerank", ["--set", "rerank=false"], "skip the cross-encoder"),
    ("dense-only", ["--set", "hybrid=false"], "FAISS only, no BM25 fusion"),
    ("k2", ["--set", "final_k=2"], "only 2 chunks of context"),
    ("no-decompose", ["--set", "decompose_multi_entity=false"], "single retrieval for multi-product questions"),
    ("no-amend-expansion", ["--set", "expand_amendments=false"], "don't pull superseding amendments into context"),
    ("no-grounding", ["--set", "grounding_check=false"], "no deterministic grounding verifier"),
    ("all-small", ["--force-route", "simple"], "every query to qwen2.5:3b"),
    ("all-large", ["--force-route", "complex"], "every query to qwen2.5:7b"),
]

COLUMNS = ["answer_accuracy", "accuracy_answerable", "abstention_accuracy", "by_type.comparison.accuracy",
           "by_type.amendment.accuracy", "retrieval.hit_rate", "retrieval.context_recall", "retrieval.mrr",
           "review.auto_answer_accuracy", "review.error_recall", "latency_ms_p50", "latency_ms_p95",
           "cost_per_1k_queries_usd"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=90)
    ap.add_argument("--only", default="", help="comma-separated variant names")
    args = ap.parse_args()
    reports = get_settings().reports_dir
    wanted = set(args.only.split(",")) if args.only else None

    results = []
    for name, extra, desc in VARIANTS:
        if wanted and name not in wanted:
            continue
        cmd = [sys.executable, "-m", "policyrag.evaluation.evaluate", "--name", f"ablation-{name}",
               "--limit", str(args.limit), "--no-judge", "--gate", *extra]
        print(f"==> {name}: {' '.join(extra) or '(defaults)'}", flush=True)
        proc = subprocess.run(cmd, cwd=PROJECT_ROOT)  # stream child output live
        rep = json.loads((reports / f"eval_ablation-{name}.json").read_text(encoding="utf-8"))
        flat = flatten(rep["summary"])
        failed = [c["metric"] for c in rep["gate"]["checks"] if not c["pass"]]
        results.append((name, desc, flat, proc.returncode == 0, failed))
        print(f"    accuracy={flat['answer_accuracy']} gate={'PASS' if proc.returncode == 0 else 'FAIL'} {failed}",
              flush=True)

    lines = [f"# Ablations ({args.limit}-case stratified subset, no judge, gate vs baseline)", "",
             "| variant | change | " + " | ".join(COLUMNS) + " | gate | failed checks |",
             "|" + "---|" * (len(COLUMNS) + 4)]
    for name, desc, flat, ok, failed in results:
        vals = " | ".join(str(flat.get(c)) for c in COLUMNS)
        lines.append(f"| {name} | {desc} | {vals} | {'PASS' if ok else 'FAIL'} | {', '.join(failed)} |")
    (reports / "ablations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {reports / 'ablations.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
