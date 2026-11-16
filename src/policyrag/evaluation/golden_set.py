"""Golden set schema + loading + stratified sampling."""
from __future__ import annotations

import json
import random
from pathlib import Path

from pydantic import BaseModel

from policyrag.config import get_settings


class FactRef(BaseModel):
    fact_id: str
    doc_ids: list[str]
    match: list[str]


class GoldenCase(BaseModel):
    id: str
    type: str                          # simple | amendment | comparison | internal | unanswerable
    question: str
    expected_answer: str
    must_contain: list[list[str]]      # every group must match (any variant within a group)
    facts: list[FactRef]
    relevant_doc_ids: list[str]
    answerable: bool
    allowed_confidentiality: list[str]
    line: str | None = None
    expected_format: str = "PolicyAnswer.v1"


def load_golden(path: Path | None = None) -> list[GoldenCase]:
    path = path or get_settings().data_dir / "golden_set.json"
    return [GoldenCase(**c) for c in json.loads(path.read_text(encoding="utf-8"))]


def stratified_sample(cases: list[GoldenCase], n: int, seed: int = 7) -> list[GoldenCase]:
    """Keep the type mix of the full set when evaluating a subset."""
    if n >= len(cases):
        return cases
    rng = random.Random(seed)
    by_type: dict[str, list[GoldenCase]] = {}
    for c in cases:
        by_type.setdefault(c.type, []).append(c)
    out = []
    for group in by_type.values():
        k = max(1, round(n * len(group) / len(cases)))
        out += rng.sample(group, min(k, len(group)))
    return sorted(out[:n], key=lambda c: c.id)
