"""Cost routing: send simple single-fact lookups to the small model, everything else to the default.

Deliberately rule-based: it is transparent, free, and easy to audit. The eval harness
reports quality per route, which is how you decide whether routing is safe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from policyrag.config import get_settings

_COMPARE = re.compile(
    r"\b(compare|comparison|versus|vs\.?|difference|differ|between|better|worse|cheaper|"
    r"which (one|plan|policy|has|is)|lower|higher|more|less|longer|shorter|faster|slower|fewer)\b", re.I)
_REASON = re.compile(r"\b(why|explain|should i|what happens|scenario|recommend|implication|pros|cons)\b", re.I)
_MULTI = re.compile(r"\?.+\?|\b(and also|as well as|in addition)\b", re.I | re.S)


@dataclass(frozen=True)
class Route:
    name: str          # "simple" | "complex"
    model: str
    reasons: tuple[str, ...]


def route(question: str) -> Route:
    s = get_settings()
    reasons = []
    if _COMPARE.search(question):
        reasons.append("comparison")
    if _REASON.search(question):
        reasons.append("reasoning")
    if _MULTI.search(question):
        reasons.append("multi-part")
    if len(question.split()) > 28:
        reasons.append("long")
    if reasons:
        return Route("complex", s.llm_default, tuple(reasons))
    return Route("simple", s.llm_small, ("single-fact lookup",))
