"""Hybrid retrieval: FAISS dense + BM25 -> reciprocal rank fusion -> cross-encoder rerank.

Access control is enforced here (before anything reaches the LLM), via the
`allowed_confidentiality` filter on chunk metadata.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from policyrag.config import Settings, get_settings
from policyrag.providers import get_embedder
from policyrag.retrieval.reranker import rerank_scores

_TOK = re.compile(r"[a-z0-9]+")
_STOP = frozenset("a an the of for to in on and or is are be by with my i do does what how much many which".split())


def bm25_tokens(text: str) -> list[str]:
    return [t for t in _TOK.findall(text.lower()) if t not in _STOP]


@dataclass
class Filters:
    allowed_confidentiality: tuple[str, ...] = ("public",)
    doc_types: tuple[str, ...] | None = None
    line: str | None = None

    def ok(self, c: dict) -> bool:
        if c["confidentiality"] not in self.allowed_confidentiality:
            return False
        if self.doc_types and c["doc_type"] not in self.doc_types:
            return False
        if self.line and c["line"] and c["line"] != self.line:
            return False
        return True

    def key(self) -> str:
        return f"{sorted(self.allowed_confidentiality)}|{self.doc_types}|{self.line}"


@dataclass
class Hit:
    chunk: dict
    dense: float | None = None
    bm25: float | None = None
    rrf: float = 0.0
    rerank: float | None = None
    expanded: bool = False  # pulled in by amendment expansion, not by the query

    @property
    def chunk_id(self) -> str:
        return self.chunk["chunk_id"]

    @property
    def score(self) -> float:
        return self.rerank if self.rerank is not None else self.rrf

    def to_dict(self) -> dict:
        return {"chunk_id": self.chunk_id, "doc_id": self.chunk["doc_id"], "title": self.chunk["title"],
                "section": self.chunk["section"], "doc_type": self.chunk["doc_type"],
                "last_updated": self.chunk["last_updated"], "text": self.chunk["text"],
                "scores": {"dense": self.dense, "bm25": self.bm25, "rrf": round(self.rrf, 5),
                           "rerank": None if self.rerank is None else round(float(self.rerank), 4)},
                "expanded": self.expanded}


@dataclass
class RetrievalResult:
    hits: list[Hit]
    candidates: int
    timings_ms: dict = field(default_factory=dict)

    @property
    def top_score(self) -> float:
        scored = [h.score for h in self.hits if not h.expanded]
        return float(max(scored)) if scored else 0.0


class Retriever:
    def __init__(self, index_dir: Path, settings: Settings | None = None):
        self.s = settings or get_settings()
        manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
        self.embedder = get_embedder()
        if manifest["embedding_model"] != self.embedder.name:
            raise RuntimeError(f"Index built with {manifest['embedding_model']!r} but current embedder is "
                               f"{self.embedder.name!r}; rebuild the index.")
        self.manifest = manifest
        self.index = faiss.read_index(str(index_dir / "index.faiss"))
        self.chunks: list[dict] = [json.loads(l) for l in (index_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l]
        self.bm25 = BM25Okapi([bm25_tokens(c["embed_text"]) for c in self.chunks])
        # doc_id -> list of chunk indices of amendments that supersede it
        self.amendments: dict[str, list[int]] = {}
        for i, c in enumerate(self.chunks):
            if c.get("supersedes"):
                self.amendments.setdefault(c["supersedes"], []).append(i)
        self.superseded_by: dict[str, list[str]] = {}
        for base, idxs in self.amendments.items():
            self.superseded_by[base] = sorted({self.chunks[i]["doc_id"] for i in idxs})
        # longest first so "Silver PPO" is matched before any shorter overlapping name
        self.products: list[str] = sorted({c["product"] for c in self.chunks if c.get("product")}, key=len, reverse=True)

    def products_in(self, text: str) -> list[str]:
        """Product names mentioned in `text`, in order of first appearance."""
        low, found = text.lower(), []
        for p in self.products:
            i = low.find(p.lower())
            if i >= 0:
                found.append((i, p))
                low = low[:i] + " " * len(p) + low[i + len(p):]
        return [p for _, p in sorted(found)]

    # ------------------------------------------------------------------ stages
    def _dense(self, query: str, k: int, flt: Filters) -> list[tuple[int, float]]:
        q = self.embedder.embed_query(query).reshape(1, -1).astype("float32")
        fetch = min(len(self.chunks), max(k * 5, 50))
        scores, idx = self.index.search(q, fetch)
        out = [(int(i), float(s)) for i, s in zip(idx[0], scores[0]) if i >= 0 and flt.ok(self.chunks[i])]
        return out[:k]

    def _sparse(self, query: str, k: int, flt: Filters) -> list[tuple[int, float]]:
        scores = self.bm25.get_scores(bm25_tokens(query))
        order = np.argsort(-scores)
        out = []
        for i in order:
            if scores[i] <= 0:
                break
            if flt.ok(self.chunks[i]):
                out.append((int(i), float(scores[i])))
                if len(out) >= k:
                    break
        return out

    def retrieve(self, query: str, flt: Filters | None = None, final_k: int | None = None,
                 hybrid: bool | None = None, rerank: bool | None = None) -> RetrievalResult:
        s = self.s
        flt = flt or Filters()
        final_k = final_k or s.final_k
        hybrid = s.hybrid if hybrid is None else hybrid
        rerank = s.rerank if rerank is None else rerank
        products = self.products_in(query) if s.decompose_multi_entity else []
        if len(products) < 2:
            top, n, t = self._retrieve_one(query, flt, final_k, hybrid, rerank)
        else:
            # Query decomposition: a single embedding of "A vs B" tends to land on one of them.
            # Retrieve per product (other names removed), then interleave so each gets context.
            per_k = max(3, final_k // len(products) + 1)
            runs, t, n = [], {}, 0
            for p in products:
                sub = query
                for other in products:
                    if other != p:
                        sub = re.sub(re.escape(other), " ", sub, flags=re.I)
                hits, cn, ct = self._retrieve_one(sub, flt, per_k * 3, hybrid, rerank)
                # entity-aware: we know which product this sub-query is about, so its own chunks go first
                hits.sort(key=lambda h: h.chunk.get("product") != p)  # stable: keeps rerank order within groups
                runs.append(hits[:per_k])
                n += cn
                for k, v in ct.items():
                    t[k] = t.get(k, 0.0) + v
            top, seen = [], set()
            for rank in range(per_k):
                for hits in runs:
                    if rank < len(hits) and hits[rank].chunk_id not in seen:
                        seen.add(hits[rank].chunk_id)
                        top.append(hits[rank])
            t["decomposed_into"] = float(len(products))
        if s.expand_amendments:
            top = self._expand_amendments(query, top, flt, rerank)
        return RetrievalResult(hits=top, candidates=n, timings_ms={k: round(v, 1) for k, v in t.items()})

    def _retrieve_one(self, query: str, flt: Filters, final_k: int, hybrid: bool,
                      rerank: bool) -> tuple[list[Hit], int, dict[str, float]]:
        s = self.s
        t: dict[str, float] = {}

        t0 = time.perf_counter()
        dense = self._dense(query, s.dense_k, flt)
        t["dense"] = (time.perf_counter() - t0) * 1000
        hits: dict[int, Hit] = {}
        for rank, (i, sc) in enumerate(dense):
            hits[i] = Hit(self.chunks[i], dense=round(sc, 4), rrf=1.0 / (s.rrf_k + rank + 1))
        if hybrid:
            t0 = time.perf_counter()
            for rank, (i, sc) in enumerate(self._sparse(query, s.bm25_k, flt)):
                h = hits.setdefault(i, Hit(self.chunks[i]))
                h.bm25 = round(sc, 3)
                h.rrf += 1.0 / (s.rrf_k + rank + 1)
            t["bm25"] = (time.perf_counter() - t0) * 1000

        cands = sorted(hits.values(), key=lambda h: -h.rrf)
        if rerank and cands:
            t0 = time.perf_counter()
            for h, sc in zip(cands, rerank_scores(query, [h.chunk["embed_text"] for h in cands])):
                h.rerank = float(sc)
            cands.sort(key=lambda h: -h.rerank)
            t["rerank"] = (time.perf_counter() - t0) * 1000
        return cands[:final_k], len(cands), t

    def _expand_amendments(self, query: str, top: list[Hit], flt: Filters, rerank: bool, limit: int = 2) -> list[Hit]:
        """If a retrieved chunk's document has been amended, make sure the amendment is in context."""
        present = {h.chunk_id for h in top}
        extra: list[int] = []
        for h in top:
            for i in self.amendments.get(h.chunk["doc_id"], []):
                if self.chunks[i]["chunk_id"] not in present and flt.ok(self.chunks[i]) and i not in extra:
                    extra.append(i)
        if not extra:
            return top
        extra_hits = [Hit(self.chunks[i], expanded=True) for i in extra]
        if rerank:
            for h, sc in zip(extra_hits, rerank_scores(query, [h.chunk["embed_text"] for h in extra_hits])):
                h.rerank = float(sc)
            extra_hits.sort(key=lambda h: -(h.rerank or 0))
        return top + extra_hits[:limit]


@lru_cache
def get_retriever() -> Retriever:
    return Retriever(get_settings().index_dir)
