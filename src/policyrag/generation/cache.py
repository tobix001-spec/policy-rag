"""Semantic answer cache with an entity guard.

Embedding similarity alone is unsafe for this domain: "deductible for Silver PPO" and
"deductible for Gold PPO" can score >0.97 cosine. A hit therefore requires ALL of:
  * cosine >= threshold
  * identical filter key (an internal-scope answer must never serve a public query)
  * identical entity signature (product names, numbers, channel words)
  * content-token Jaccard >= 0.5
Only confident, answered results are cached; review-queue items never are.
"""
from __future__ import annotations

import json
import re
import threading
import time
import uuid
from dataclasses import dataclass

import numpy as np

from policyrag.config import get_settings

_TOK = re.compile(r"[a-z0-9]+")
_NUM = re.compile(r"\d+(?:\.\d+)?")
_STOP = frozenset("a an the of for to in on and or is are be by with my i do does what how much many which "
                  "can will me it its at this that there their our your you we".split())
CHANNEL_WORDS = frozenset({"mobile", "app", "web", "website", "portal", "phone", "internal", "email", "chat"})


def content_tokens(q: str) -> set[str]:
    return {t for t in _TOK.findall(q.lower()) if t not in _STOP}


class EntitySignature:
    def __init__(self, product_names: list[str]):
        # longest first so "Silver PPO" wins over "Silver"
        self.products = sorted({p.lower() for p in product_names if p}, key=len, reverse=True)

    def __call__(self, q: str) -> str:
        ql = q.lower()
        found = []
        for p in self.products:
            if p in ql:
                found.append(p)
                ql = ql.replace(p, " ")
        nums = _NUM.findall(q)
        chans = sorted(CHANNEL_WORDS & set(_TOK.findall(q.lower())))
        return json.dumps([sorted(found), sorted(nums), chans])


@dataclass
class CacheEntry:
    id: str
    question: str
    vec: np.ndarray
    filter_key: str
    signature: str
    tokens: set[str]
    payload: dict
    created: float


class SemanticCache:
    def __init__(self, signature: EntitySignature, threshold: float | None = None,
                 ttl_s: int | None = None, max_entries: int | None = None):
        s = get_settings()
        self.sig = signature
        self.threshold = threshold if threshold is not None else s.cache_similarity
        self.ttl = ttl_s if ttl_s is not None else s.cache_ttl_s
        self.max_entries = max_entries or s.cache_max_entries
        self._entries: list[CacheEntry] = []
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.guard_rejections = 0

    def _live(self) -> list[CacheEntry]:
        now = time.time()
        self._entries = [e for e in self._entries if now - e.created < self.ttl]
        return self._entries

    def get(self, question: str, vec: np.ndarray, filter_key: str) -> tuple[dict, float] | None:
        with self._lock:
            entries = self._live()
            if not entries:
                self.misses += 1
                return None
            mat = np.stack([e.vec for e in entries])
            sims = mat @ vec
            sig = self.sig(question)
            toks = content_tokens(question)
            for i in np.argsort(-sims):
                if sims[i] < self.threshold:
                    break
                e = entries[i]
                jac = len(toks & e.tokens) / max(len(toks | e.tokens), 1)
                if e.filter_key == filter_key and e.signature == sig and jac >= 0.5:
                    self.hits += 1
                    return e.payload, float(sims[i])
                self.guard_rejections += 1
            self.misses += 1
            return None

    def put(self, question: str, vec: np.ndarray, filter_key: str, payload: dict) -> None:
        with self._lock:
            self._live()
            self._entries.append(CacheEntry(uuid.uuid4().hex, question, vec.astype("float32"), filter_key,
                                            self.sig(question), content_tokens(question), payload, time.time()))
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict:
        return {"entries": len(self._entries), "hits": self.hits, "misses": self.misses,
                "guard_rejections": self.guard_rejections, "threshold": self.threshold}


class RedisSemanticCache(SemanticCache):
    """Same semantics, entries persisted in Redis so multiple API replicas share them.

    Lookup scans entries client-side, which is fine for thousands of entries; at larger
    scale, swap in Redis vector search (FT.SEARCH KNN) behind the same interface.
    """

    PREFIX = "policyrag:cache:"

    def __init__(self, signature: EntitySignature, url: str, **kw):
        super().__init__(signature, **kw)
        import redis

        self.r = redis.Redis.from_url(url)

    def _live(self) -> list[CacheEntry]:
        out = []
        for key in self.r.scan_iter(self.PREFIX + "*"):
            raw = self.r.get(key)
            if not raw:
                continue
            d = json.loads(raw)
            out.append(CacheEntry(d["id"], d["question"], np.asarray(d["vec"], dtype="float32"), d["filter_key"],
                                  d["signature"], set(d["tokens"]), d["payload"], d["created"]))
        return out

    def put(self, question: str, vec: np.ndarray, filter_key: str, payload: dict) -> None:
        eid = uuid.uuid4().hex
        d = {"id": eid, "question": question, "vec": vec.astype(float).tolist(), "filter_key": filter_key,
             "signature": self.sig(question), "tokens": sorted(content_tokens(question)), "payload": payload,
             "created": time.time()}
        self.r.set(self.PREFIX + eid, json.dumps(d), ex=self.ttl)

    def clear(self) -> None:
        for key in self.r.scan_iter(self.PREFIX + "*"):
            self.r.delete(key)

    def stats(self) -> dict:
        st = super().stats()
        st["entries"] = sum(1 for _ in self.r.scan_iter(self.PREFIX + "*"))
        return st
