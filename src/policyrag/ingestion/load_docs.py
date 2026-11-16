"""Load raw documents (Markdown with front matter, TXT, PDF) into a uniform record."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_FM = re.compile(r"^---\n(.*?)\n---\n", re.S)


@dataclass
class RawDoc:
    doc_id: str
    text: str
    source: str
    metadata: dict = field(default_factory=dict)


def _parse_front_matter(text: str) -> tuple[dict, str]:
    m = _FM.match(text)
    if not m:
        return {}, text
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        try:
            meta[k.strip()] = json.loads(v)
        except json.JSONDecodeError:
            meta[k.strip()] = v.strip("'\"")
    return meta, text[m.end():]


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("PDF support needs `pip install pypdf`") from e
    return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def load_documents(raw_dir: Path) -> list[RawDoc]:
    docs: list[RawDoc] = []
    for path in sorted(raw_dir.rglob("*")):
        suffix = path.suffix.lower()
        if suffix not in {".md", ".txt", ".pdf"}:
            continue
        text = _read_pdf(path) if suffix == ".pdf" else path.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(text) if suffix == ".md" else ({}, text)
        meta.setdefault("doc_id", path.stem)
        meta.setdefault("title", path.stem.replace("-", " ").title())
        meta.setdefault("doc_type", "support")
        meta.setdefault("confidentiality", "public")
        meta.setdefault("last_updated", "")
        docs.append(RawDoc(doc_id=meta["doc_id"], text=body, source=str(path.relative_to(raw_dir)), metadata=meta))
    return docs
