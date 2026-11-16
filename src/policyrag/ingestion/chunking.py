"""Structure-aware semantic chunking with a recursive-character fallback.

1. Split on Markdown headings so a chunk never straddles two sections.
2. Inside a section, split into sentences (bullet lists stay together), embed them,
   and break where the cosine distance between neighbours exceeds the document's
   Nth-percentile distance (the same idea as LangChain's SemanticChunker, but
   batched across the whole corpus so ingest embeds every sentence once).
3. Merge pieces shorter than `min_chars`; send pieces longer than `max_chars` to
   RecursiveCharacterTextSplitter.
4. Prefix each chunk with "title | section" for embedding (a contextual header), which
   matters here: sibling products use near-identical sentences.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

from policyrag.ingestion.load_docs import RawDoc
from policyrag.providers import Embedder

_HEADING = re.compile(r"^(#{1,3})\s+(.+)$", re.M)
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"(])")


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    embed_text: str
    title: str
    section: str
    doc_type: str
    line: str
    product: str
    last_updated: str
    confidentiality: str
    supersedes: str
    source: str
    position: int

    def to_dict(self) -> dict:
        return asdict(self)


def split_sections(text: str) -> list[tuple[str, str]]:
    """[(section_heading, body)], skipping the H1 title line."""
    out: list[tuple[str, str]] = []
    matches = list(_HEADING.finditer(text))
    if not matches:
        return [("Body", text.strip())] if text.strip() else []
    pre = text[: matches[0].start()].strip()
    if pre:
        out.append(("Preamble", pre))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end(): end].strip()
        if len(m.group(1)) == 1:  # H1 = title; keep any body under it
            if body:
                out.append(("Introduction", body))
            continue
        if body:
            out.append((m.group(2).strip(), body))
    return out


def split_units(body: str) -> list[str]:
    """Sentence-ish units. Paragraphs that are lists are kept whole."""
    units: list[str] = []
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para:
            continue
        if re.search(r"^\s*[-*]\s", para, re.M):
            units.append(para)
        else:
            units.extend(s.strip() for s in _SENT.split(para) if s.strip())
    return units


class SemanticChunker:
    def __init__(self, embedder: Embedder | None, breakpoint_percentile: float = 85.0,
                 min_chars: int = 200, max_chars: int = 1200, overlap_chars: int = 120):
        self.embedder = embedder
        self.pct = breakpoint_percentile
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.fallback = RecursiveCharacterTextSplitter(
            chunk_size=max_chars, chunk_overlap=overlap_chars, separators=["\n\n", "\n", ". ", " ", ""])

    # -------------------------------------------------------------- grouping
    def _group(self, units: list[str], dists: np.ndarray, threshold: float) -> list[str]:
        groups, cur = [], [units[0]]
        for i, u in enumerate(units[1:]):
            if dists[i] > threshold and sum(map(len, cur)) >= self.min_chars:
                groups.append(" ".join(cur))
                cur = [u]
            else:
                cur.append(u)
        groups.append(" ".join(cur))
        merged: list[str] = []
        for g in groups:  # glue undersized trailing groups onto the previous one
            if merged and len(g) < self.min_chars and len(merged[-1]) + len(g) <= self.max_chars:
                merged[-1] += " " + g
            else:
                merged.append(g)
        out: list[str] = []
        for g in merged:
            out.extend(self.fallback.split_text(g) if len(g) > self.max_chars else [g])
        return out

    def chunk_documents(self, docs: list[RawDoc]) -> list[Chunk]:
        # 1) sections + units for every doc
        plan: list[tuple[RawDoc, list[tuple[str, list[str]]]]] = []
        all_units: list[str] = []
        for d in docs:
            secs = [(h, split_units(b)) for h, b in split_sections(d.text)]
            secs = [(h, u) for h, u in secs if u]
            plan.append((d, secs))
            for _, u in secs:
                all_units.extend(u)

        # 2) one batched embedding pass over every unit in the corpus
        vecs = self.embedder.embed_documents(all_units) if (self.embedder and all_units) else None

        chunks: list[Chunk] = []
        cursor = 0
        for d, secs in plan:
            # per-document breakpoint threshold from all adjacent-unit distances in that document
            doc_dists: list[np.ndarray] = []
            spans = []
            for _, units in secs:
                n = len(units)
                if vecs is not None and n > 1:
                    v = vecs[cursor: cursor + n]
                    dd = 1.0 - np.sum(v[:-1] * v[1:], axis=1)
                else:
                    dd = np.zeros(max(n - 1, 0), dtype="float32")
                doc_dists.append(dd)
                spans.append((cursor, n))
                cursor += n
            flat = np.concatenate(doc_dists) if doc_dists else np.zeros(0)
            threshold = float(np.percentile(flat, self.pct)) if flat.size else 1.0

            pos = 0
            meta = d.metadata
            carry: tuple[str, str] | None = None  # undersized section waiting to merge forward
            for si, ((heading, units), dd) in enumerate(zip(secs, doc_dists)):
                if vecs is None:
                    pieces = self.fallback.split_text(" ".join(units))
                else:
                    pieces = self._group(units, dd, threshold)
                if carry:
                    pieces[0] = f"{carry[1]}\n\n{pieces[0]}"
                    heading = f"{carry[0]} / {heading}"
                    carry = None
                is_last = si == len(secs) - 1
                if len(pieces) == 1 and len(pieces[0]) < self.min_chars and not is_last:
                    carry = (heading, pieces[0])
                    continue
                if is_last and len(pieces) == 1 and len(pieces[0]) < self.min_chars and chunks \
                        and chunks[-1].doc_id == d.doc_id and len(chunks[-1].text) + len(pieces[0]) <= self.max_chars:
                    prev = chunks[-1]  # tiny closing section: fold into the previous chunk of this doc
                    prev.text = f"{prev.text}\n\n{pieces[0]}"
                    prev.section = f"{prev.section} / {heading}"
                    prev.embed_text = f"{prev.title} | {prev.section}\n{prev.text}"
                    continue
                for p in pieces:
                    title = str(meta.get("title", d.doc_id))
                    chunks.append(Chunk(
                        chunk_id=f"{d.doc_id}#c{pos}", doc_id=d.doc_id, text=p,
                        embed_text=f"{title} | {heading}\n{p}", title=title, section=heading,
                        doc_type=str(meta.get("doc_type", "")), line=str(meta.get("line", "")),
                        product=str(meta.get("product", "")), last_updated=str(meta.get("last_updated", "")),
                        confidentiality=str(meta.get("confidentiality", "public")),
                        supersedes=str(meta.get("supersedes", "")), source=d.source, position=pos,
                    ))
                    pos += 1
        return chunks
