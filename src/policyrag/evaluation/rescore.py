"""Re-grade stored eval reports with the current grader, without re-running any model.

    python -m policyrag.evaluation.rescore

Used when the grader is fixed (e.g. comparison answers must now name the correct winner), so every
historical version is judged by the same rule. Gates are recomputed: v1 vs v0, ablations vs v1.
"""
from __future__ import annotations

import json

import yaml

from policyrag.config import get_settings
from policyrag.evaluation.ablations import COLUMNS, VARIANTS
from policyrag.evaluation.evaluate import (
    GATE_FILE, comparison_winner_ok, flatten, run_gate, summarize, write_markdown,
)
from policyrag.evaluation.golden_set import load_golden
from policyrag.textnorm import contains_all_groups


def rescore(path, baseline_summary: dict | None, gate_cfg: dict, golden: dict) -> dict:
    rep = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for r in rep["rows"]:
        if r["type"] != "comparison":
            continue
        case = golden[r["id"]]
        # rebuilt from scratch every time, so re-running this script is idempotent
        values_ok = (not r["abstained"]) and contains_all_groups(r["answer"], case.must_contain)
        new = values_ok and comparison_winner_ok(r["answer"], case.expected_answer, case.question)
        changed += int(new != values_ok)
        r["correct"] = new
    rep["summary"] = summarize(rep["rows"])
    if baseline_summary is not None:
        passed, checks = run_gate(rep["summary"], baseline_summary, gate_cfg)
        rep["gate"] = {"passed": passed, "checks": checks, "baseline": rep.get("gate", {}).get("baseline")}
    rep["rescored"] = {"grader": "comparison winner check", "rows_changed": changed}
    path.write_text(json.dumps(rep, indent=2, default=str), encoding="utf-8")
    write_markdown(path.with_suffix(".md"), rep)
    print(f"{path.name:<40} {changed} comparison rows -> wrong   accuracy={rep['summary']['answer_accuracy']}")
    return rep


def main() -> None:
    rd = get_settings().reports_dir
    gate_cfg = yaml.safe_load(GATE_FILE.read_text(encoding="utf-8"))
    golden = {c.id: c for c in load_golden()}
    v0 = rescore(rd / "eval_v0-baseline.json", None, gate_cfg, golden)
    v1 = rescore(rd / "eval_v1.json", v0["summary"], gate_cfg, golden)
    if (rd / "eval_v2.json").exists():
        rescore(rd / "eval_v2.json", v1["summary"], gate_cfg, golden)
    (rd / "baseline_v0.json").write_text(json.dumps({"from": "eval_v0-baseline.json", "summary": v0["summary"]},
                                                    indent=2), encoding="utf-8")
    (rd / "baseline.json").write_text(json.dumps({"from": "eval_v1.json", "summary": v1["summary"]}, indent=2),
                                      encoding="utf-8")

    lines = ["# Ablations (90-case stratified subset, no judge, gate vs baseline v1; re-scored with winner check)",
             "", "| variant | change | " + " | ".join(COLUMNS) + " | gate | failed checks |",
             "|" + "---|" * (len(COLUMNS) + 4)]
    for name, _, desc in VARIANTS:
        p = rd / f"eval_ablation-{name}.json"
        if not p.exists():
            continue
        rep = rescore(p, v1["summary"], gate_cfg, golden)
        flat = flatten(rep["summary"])
        failed = sorted({c["metric"] for c in rep["gate"]["checks"] if not c["pass"]})
        lines.append(f"| {name} | {desc} | " + " | ".join(str(flat.get(c)) for c in COLUMNS) +
                     f" | {'PASS' if rep['gate']['passed'] else 'FAIL'} | {', '.join(failed)} |")
    (rd / "ablations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
