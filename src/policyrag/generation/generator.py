"""AnswerService: the full query path.

cache -> hybrid retrieve + rerank -> route -> LCEL (prompt | llm.with_retry().with_fallbacks())
      -> Pydantic validation (+1 repair pass) -> citation check -> confidence -> review queue
      -> metrics/logging -> cache store
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.messages import AIMessage
from pydantic import ValidationError

from policyrag.config import get_settings
from policyrag.generation import router
from policyrag.generation.cache import EntitySignature, RedisSemanticCache, SemanticCache
from policyrag.generation.prompts import (
    ABSTAIN_TEXT, ANSWER_JSON_SCHEMA, ANSWER_PROMPT, REPAIR_PROMPT, SCHEMA_VERSION, LLMAnswer, format_context,
    schema_text,
)
from policyrag.generation.review_queue import ReviewQueue
from policyrag.monitoring import metrics as M
from policyrag.providers import get_chat_model, usage_from_message
from policyrag.retrieval.retriever import Filters, Retriever, get_retriever

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


@dataclass
class ParseOutcome:
    answer: LLMAnswer | None
    valid_first_try: bool
    repaired: bool
    error: str | None
    extra_in: int = 0
    extra_out: int = 0
    coerced: tuple[str, ...] = ()


def coerce(text: str) -> tuple[str, tuple[str, ...]]:
    """Deterministic, logged fixes for known small-model quirks (cheaper than an LLM repair call).

    Ollama's schema-constrained decoding enforces types but not numeric bounds, so small models
    sometimes emit confidence as a percentage (e.g. 99).
    """
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return text, ()
    fixes = []
    if isinstance(obj, dict):
        c = obj.get("confidence")
        if isinstance(c, (int, float)) and 1 < c <= 100:
            obj["confidence"] = c / 100.0
            fixes.append("confidence_percent_to_fraction")
        if isinstance(obj.get("sources"), str):
            obj["sources"] = [obj["sources"]]
            fixes.append("sources_str_to_list")
    return (json.dumps(obj), tuple(fixes)) if fixes else (text, ())


_NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?%?")


def _numbers(text: str) -> set[str]:
    out = set()
    for m in _NUMBER.finditer(text):
        n = m.group(0).replace(",", "").replace("$", "").rstrip("%").rstrip(".")
        out.add(n.lstrip("0") or "0")  # "June 03" and "June 3" are the same number
    return out


def grounding_issues(question: str, answer: str, cited_texts: list[str], products: list[str]) -> list[str]:
    """Deterministic verifier. LLM self-reported confidence is poorly calibrated (wrong answers
    routinely claim 0.9+), so we check the two things that matter most in this domain:
      * every number in the answer appears in a cited chunk (and is not merely echoed from the question)
      * every product named in the question appears in at least one cited chunk
    """
    issues = []
    cited = " ".join(cited_texts)
    missing = _numbers(answer) - _numbers(cited) - _numbers(question)
    if missing:
        issues.append("ungrounded_number")
    low = cited.lower()
    if any(p.lower() not in low for p in products):
        issues.append("product_not_in_sources")
    return issues


class AnswerService:
    def __init__(self, retriever: Retriever | None = None, review: ReviewQueue | None = None,
                 cache: SemanticCache | None = None, log: M.QueryLog | None = None):
        self.s = get_settings()
        self.retriever = retriever or get_retriever()
        self.review = review or ReviewQueue(self.s.review_db)
        if cache is None and self.s.cache_enabled:
            sig = EntitySignature([c["product"] for c in self.retriever.chunks])
            cache = (RedisSemanticCache(sig, self.s.redis_url) if self.s.cache_backend == "redis"
                     else SemanticCache(sig))
        self.cache = cache
        self.log = log or M.QueryLog()

    # ------------------------------------------------------------------ LLM call with retry + fallback
    def _invoke(self, model: str, context: str, question: str) -> tuple[AIMessage, str, bool]:
        primary = get_chat_model(model, ANSWER_JSON_SCHEMA)
        alt_name = self.s.llm_small if model == self.s.llm_default else self.s.llm_default
        fallback = get_chat_model(alt_name, ANSWER_JSON_SCHEMA)
        chain = ANSWER_PROMPT | primary.with_retry(stop_after_attempt=2, wait_exponential_jitter=True) \
            .with_fallbacks([fallback.with_retry(stop_after_attempt=1)])
        msg: AIMessage = chain.invoke({"context": context, "question": question})
        used = (msg.response_metadata or {}).get("model") or model  # Ollama reports the model that answered
        used_fallback = self.s.provider != "fake" and used != model
        if used_fallback:
            M.FALLBACKS.inc()
        return msg, (alt_name if used_fallback else model), used_fallback

    def _parse(self, raw: str, model: str) -> ParseOutcome:
        text = _FENCE.sub("", raw.strip())
        try:
            return ParseOutcome(LLMAnswer.model_validate_json(text), True, False, None)
        except ValidationError as e:
            err = str(e)[:800]
        text, fixes = coerce(text)
        if fixes:
            try:
                return ParseOutcome(LLMAnswer.model_validate_json(text), False, False, None, coerced=fixes)
            except ValidationError as e:
                err = str(e)[:800]
        if self.s.max_json_repairs < 1:
            M.JSON_REPAIRS.labels("disabled").inc()
            return ParseOutcome(None, False, False, err)
        try:
            msg = (REPAIR_PROMPT | get_chat_model(model, ANSWER_JSON_SCHEMA)).invoke(
                {"error": err, "output": raw[:4000], "schema": schema_text()})
            i, o = usage_from_message(msg)
            ans = LLMAnswer.model_validate_json(_FENCE.sub("", str(msg.content).strip()))
            M.JSON_REPAIRS.labels("fixed").inc()
            return ParseOutcome(ans, False, True, None, i, o)
        except Exception as e:  # noqa: BLE001 - any failure here means "non-compliant output"
            M.JSON_REPAIRS.labels("failed").inc()
            return ParseOutcome(None, False, False, f"{err}; repair failed: {e}")

    # ------------------------------------------------------------------ main entry point
    def answer(self, question: str, filters: Filters | None = None, use_cache: bool = True,
               force_route: str | None = None, retrieval_overrides: dict | None = None) -> dict:
        t_start = time.perf_counter()
        rid = uuid.uuid4().hex[:12]
        flt = filters or Filters()
        timings: dict[str, float] = {}

        # ---- cache
        qvec = None
        if use_cache and self.cache is not None:
            t0 = time.perf_counter()
            qvec = self.retriever.embedder.embed_query(question)
            hit = self.cache.get(question, qvec, flt.key())
            timings["cache_lookup"] = (time.perf_counter() - t0) * 1000
            if hit:
                payload, sim = hit
                out = {**payload, "request_id": rid, "question": question,
                       "cache": {"hit": True, "similarity": round(sim, 4), "original_question": payload["question"]},
                       "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd_estimate": 0.0},
                       "latency_ms": {"total": round((time.perf_counter() - t_start) * 1000, 1), **timings}}
                M.QUERIES.labels(payload["route"]["name"], payload["status"], "hit").inc()
                M.LATENCY.labels("cache").observe(out["latency_ms"]["total"] / 1000)
                self.log.record({"request_id": rid, "question": question, "cache_hit": True,
                                 "latency_ms": out["latency_ms"]["total"], "cost_usd": 0.0, "status": out["status"]})
                return out

        # ---- retrieve
        t0 = time.perf_counter()
        ret = self.retriever.retrieve(question, flt, **(retrieval_overrides or {}))
        timings["retrieval"] = (time.perf_counter() - t0) * 1000
        timings.update({f"retrieval.{k}": v for k, v in ret.timings_ms.items()})
        M.STAGE.labels("retrieval").observe(timings["retrieval"] / 1000)

        # ---- route + generate
        rt = router.route(question)
        if self.s.context_routing and rt.name == "simple":
            # post-retrieval routing: a relevant amendment means conflicting values in context,
            # which the small model resolves poorly (measured in eval v0)
            if any(h.chunk.get("supersedes") and not h.expanded and (h.rerank or 0) >= 0.5 for h in ret.hits):
                rt = router.Route("complex", self.s.llm_default, ("amendment_in_context",))
        if force_route == "simple":
            rt = router.Route("simple", self.s.llm_small, ("forced",))
        elif force_route == "complex":
            rt = router.Route("complex", self.s.llm_default, ("forced",))
        context = format_context(ret.hits, self.retriever.superseded_by)
        t0 = time.perf_counter()
        error = None
        try:
            msg, model_used, used_fallback = self._invoke(rt.model, context, question)
            raw = str(msg.content)
            in_tok, out_tok = usage_from_message(msg)
        except Exception as e:  # noqa: BLE001 - both models failed: degrade gracefully, never 500
            M.ERRORS.labels("llm_unavailable").inc()
            error = f"LLM unavailable: {type(e).__name__}: {e}"
            msg, model_used, used_fallback, raw, in_tok, out_tok = None, rt.model, True, "", 0, 0
        timings["llm"] = (time.perf_counter() - t0) * 1000
        M.STAGE.labels("llm").observe(timings["llm"] / 1000)

        parsed = self._parse(raw, model_used) if raw else ParseOutcome(None, False, False, error or "empty output")
        in_tok += parsed.extra_in
        out_tok += parsed.extra_out
        ans = parsed.answer

        # ---- citations + confidence
        retrieved_ids = {h.chunk_id for h in ret.hits}
        hit_map = {h.chunk_id: h for h in ret.hits}
        doc_first_chunk = {}
        for h in ret.hits:
            doc_first_chunk.setdefault(h.chunk["doc_id"], h.chunk_id)
        valid, invalid = [], []
        for sid in (ans.sources if ans else []):
            sid = sid.strip().strip("[]")
            if sid in retrieved_ids:
                valid.append(sid)
            elif sid in doc_first_chunk:  # model cited a doc_id instead of a chunk_id
                valid.append(doc_first_chunk[sid])
            else:
                invalid.append(sid)
        valid = list(dict.fromkeys(valid))

        if ret.hits and any(h.rerank is not None for h in ret.hits):
            retrieval_conf = ret.top_score
        else:
            retrieval_conf = max((h.dense or 0.0 for h in ret.hits), default=0.0)
        llm_conf = ans.confidence if ans else 0.0
        conf = self.s.confidence_w_retrieval * retrieval_conf + self.s.confidence_w_llm * llm_conf
        reasons: list[str] = []
        if ans is None:
            reasons.append("invalid_output")
            conf = 0.0
        elif not ans.answerable:
            reasons.append("abstained")
            conf = min(conf, 0.3)
        else:
            if not valid:
                reasons.append("no_valid_citation")
                conf *= 0.5
            if invalid:
                reasons.append("invalid_citation")
                conf *= 0.8
            if self.s.grounding_check and valid:
                cited_texts = [f"{hit_map[c].chunk['title']}\n{hit_map[c].chunk['text']}" for c in valid]
                issues = grounding_issues(question, ans.answer, cited_texts, self.retriever.products_in(question))
                if issues:
                    reasons.extend(issues)
                    conf *= 0.6
        if conf < self.s.confidence_threshold and "abstained" not in reasons and "invalid_output" not in reasons:
            reasons.append("low_confidence")
        status = "needs_review" if reasons else "answered"

        cost = M.cost_usd(model_used, in_tok, out_tok)
        hit_by_id = {h.chunk_id: h for h in ret.hits}
        out = {
            "request_id": rid, "schema_version": SCHEMA_VERSION, "question": question,
            "answer": ans.answer if ans else ABSTAIN_TEXT,
            "answerable": bool(ans.answerable) if ans else False,
            "reasoning": ans.reasoning if ans else (error or parsed.error or ""),
            "sources": [{"chunk_id": c, "doc_id": hit_by_id[c].chunk["doc_id"], "title": hit_by_id[c].chunk["title"],
                         "section": hit_by_id[c].chunk["section"], "last_updated": hit_by_id[c].chunk["last_updated"],
                         "snippet": hit_by_id[c].chunk["text"][:300], "rerank_score": hit_by_id[c].rerank}
                        for c in valid],
            "invalid_citations": invalid,
            "confidence": {"final": round(conf, 4), "retrieval": round(retrieval_conf, 4), "llm": round(llm_conf, 4),
                           "threshold": self.s.confidence_threshold},
            "status": status, "review_reasons": reasons, "review_id": None,
            "route": {"name": rt.name, "model": model_used, "reasons": list(rt.reasons), "fallback_used": used_fallback},
            "usage": {"input_tokens": in_tok, "output_tokens": out_tok, "cost_usd_estimate": round(cost, 8)},
            "format": {"valid_first_try": parsed.valid_first_try, "repaired": parsed.repaired,
                       "coerced": list(parsed.coerced), "valid": ans is not None, "error": parsed.error},
            "retrieved": [h.to_dict() for h in ret.hits],
            "cache": {"hit": False},
            "filters": {"allowed_confidentiality": list(flt.allowed_confidentiality), "doc_types": flt.doc_types,
                        "line": flt.line},
            "raw_output": raw,
        }
        if status == "needs_review":
            public = {k: v for k, v in out.items() if k not in ("retrieved", "raw_output")}
            out["review_id"] = self.review.enqueue(question, public, conf, reasons)
            M.REVIEW_OPEN.set(self.review.counts().get("open", 0))

        out["latency_ms"] = {"total": round((time.perf_counter() - t_start) * 1000, 1),
                             **{k: round(v, 1) for k, v in timings.items()}}

        M.QUERIES.labels(rt.name, status, "miss").inc()
        M.LATENCY.labels(rt.name).observe(out["latency_ms"]["total"] / 1000)
        M.TOKENS.labels(model_used, "input").inc(in_tok)
        M.TOKENS.labels(model_used, "output").inc(out_tok)
        M.COST.labels(model_used).inc(cost)
        self.log.record({"request_id": rid, "question": question, "cache_hit": False, "route": rt.name,
                         "model": model_used, "fallback": used_fallback, "status": status, "reasons": reasons,
                         "confidence": out["confidence"]["final"], "input_tokens": in_tok, "output_tokens": out_tok,
                         "cost_usd": cost, "latency_ms": out["latency_ms"]["total"], "timings": out["latency_ms"]})

        if use_cache and self.cache is not None and status == "answered":
            cacheable = {k: v for k, v in out.items() if k not in ("request_id", "latency_ms", "usage", "cache")}
            self.cache.put(question, qvec if qvec is not None else self.retriever.embedder.embed_query(question),
                           flt.key(), cacheable)
        return out


@lru_cache
def get_service() -> AnswerService:
    return AnswerService()
