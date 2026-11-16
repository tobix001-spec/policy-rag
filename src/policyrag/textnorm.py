"""Text normalization shared by the corpus generator and the evaluator, so
'$1,500', '1500 dollars' and '$1500' all compare equal."""
from __future__ import annotations

import re

_DIGIT_COMMA = re.compile(r"(?<=\d),(?=\d{3})")
_WS = re.compile(r"\s+")


def norm(text: str) -> str:
    t = text.lower()
    t = t.replace("–", "-").replace("—", "-").replace(" ", " ")
    t = _DIGIT_COMMA.sub("", t)
    t = t.replace("$ ", "$")
    return _WS.sub(" ", t).strip()


def _pattern(variant: str) -> re.Pattern:
    # boundaries so "$1500" does not match inside "$15000" and "20 days" not inside "120 days"
    return re.compile(r"(?<![0-9a-z.])" + re.escape(norm(variant)) + r"(?![0-9]|\.[0-9])")


def contains_any(text: str, variants: list[str]) -> bool:
    nt = norm(text)
    return any(_pattern(v).search(nt) for v in variants)


def contains_all_groups(text: str, groups: list[list[str]]) -> bool:
    return all(contains_any(text, g) for g in groups)


def match_variants(kind: str, v: int) -> list[str]:
    """Acceptable surface forms for a numeric fact."""
    if kind == "money":
        return [f"${v}", f"{v} dollars", f"usd {v}"]
    if kind == "days":
        return [f"{v} days", f"{v}-day", f"{v} calendar days", f"{v} day"]
    if kind == "pct":
        return [f"{v}%", f"{v} percent", f"{v} %"]
    if kind == "hours":
        return [f"{v} hours", f"{v}-hour", f"{v} hrs"]
    if kind == "months":
        return [f"{v} months", f"{v}-month"]
    if kind == "years":
        return [f"{v} years", f"{v}-year", f"age {v}", f"{v} yrs"]
    if kind == "calls":
        return [f"{v} service calls", f"{v} calls", f"{v} times", f"{v} roadside"]
    if kind == "claims":
        return [f"{v} claims"]
    return [str(v)]
