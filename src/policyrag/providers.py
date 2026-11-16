"""Model providers: embeddings, cross-encoder, chat LLMs.

`local` uses sentence-transformers on GPU/CPU and Ollama for chat.
`fake` gives deterministic, dependency-free stand-ins so unit tests and CI run with
no GPU, no model downloads and no Ollama server.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from typing import Any, Protocol

import numpy as np
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from policyrag.config import Settings, get_settings

_WORD = re.compile(r"[a-z0-9$%.]+")


def l2_normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype="float32")
    if x.ndim == 1:
        x = x[None, :]
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms


def resolve_device(pref: str) -> str:
    if pref != "auto":
        return pref
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:  # pragma: no cover
        return "cpu"


# --------------------------------------------------------------------------- embeddings
class Embedder(Protocol):
    name: str
    dim: int

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...


class LocalEmbedder:
    def __init__(self, settings: Settings):
        from sentence_transformers import SentenceTransformer

        self.name = settings.embedding_model
        self._instruction = settings.embedding_query_instruction
        self._model = SentenceTransformer(settings.embedding_model, device=resolve_device(settings.device))
        get_dim = getattr(self._model, "get_embedding_dimension", None) or self._model.get_sentence_embedding_dimension
        self.dim = get_dim()

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        vecs = self._model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
        return l2_normalize(vecs)

    def embed_query(self, text: str) -> np.ndarray:
        vec = self._model.encode([self._instruction + text], normalize_embeddings=True, show_progress_bar=False)
        return l2_normalize(vec)[0]


class FakeEmbedder:
    """Hashed bag of unigrams+bigrams. Lexical, deterministic, good enough for tests."""

    def __init__(self, dim: int = 384):
        self.name = "fake-embedder"
        self.dim = dim

    def _vec(self, text: str) -> np.ndarray:
        toks = _WORD.findall(text.lower())
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        v = np.zeros(self.dim, dtype="float32")
        for f in feats:
            h = int(hashlib.md5(f.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0 if (h >> 64) & 1 else -1.0
        return v

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return l2_normalize(np.stack([self._vec(t) for t in texts])) if texts else np.zeros((0, self.dim), "float32")

    def embed_query(self, text: str) -> np.ndarray:
        return l2_normalize(self._vec(text))[0]


@lru_cache
def get_embedder() -> Embedder:
    s = get_settings()
    return FakeEmbedder() if s.provider == "fake" else LocalEmbedder(s)


# --------------------------------------------------------------------------- reranker
class CrossEncoderReranker:
    def __init__(self, settings: Settings):
        from sentence_transformers import CrossEncoder

        self.name = settings.reranker_model
        self._model = CrossEncoder(settings.reranker_model, device=resolve_device(settings.device), max_length=512)

    def score(self, query: str, passages: list[str]) -> np.ndarray:
        if not passages:
            return np.zeros(0, dtype="float32")
        import torch

        # sentence-transformers >= 4 applies Sigmoid by default; ask for raw logits and squash once ourselves
        logits = self._model.predict([(query, p) for p in passages], batch_size=32, show_progress_bar=False,
                                     activation_fn=torch.nn.Identity(), convert_to_numpy=True)
        return np.asarray(logits, dtype="float32").reshape(-1)


class FakeReranker:
    """Token-overlap scorer returning pseudo-logits."""

    name = "fake-reranker"

    def score(self, query: str, passages: list[str]) -> np.ndarray:
        q = set(_WORD.findall(query.lower()))
        out = []
        for p in passages:
            t = set(_WORD.findall(p.lower()))
            out.append(8.0 * len(q & t) / (len(q) or 1) - 4.0)
        return np.asarray(out, dtype="float32")


@lru_cache
def get_reranker():
    s = get_settings()
    return FakeReranker() if s.provider == "fake" else CrossEncoderReranker(s)


# --------------------------------------------------------------------------- chat models
_CHUNK_HDR = re.compile(r"^\[(?P<id>[^\]\s]+)\]", re.M)


class FakeChatModel(BaseChatModel):
    """Answers by extracting the context sentence with the highest word overlap.

    Understands two prompt shapes: the RAG answer prompt (context blocks headed by
    `[chunk_id]`) and judge prompts (returns a neutral verdict). Emits usage metadata
    so cost/token accounting paths are exercised in tests.
    """

    model_name: str = "fake-llm"

    @property
    def _llm_type(self) -> str:
        return "fake-chat"

    def _generate(self, messages: list[BaseMessage], stop=None,
                  run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        prompt = "\n".join(str(m.content) for m in messages)
        if "JUDGE_TASK" in prompt:
            content = json.dumps({"claims": [{"claim": "stub", "supported": True}], "questions": ["stub question?"]})
        else:
            content = self._answer(prompt)
        usage = {"input_tokens": len(prompt) // 4, "output_tokens": len(content) // 4,
                 "total_tokens": (len(prompt) + len(content)) // 4}
        msg = AIMessage(content=content, usage_metadata=usage,
                        response_metadata={"model": self.model_name})
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @staticmethod
    def _answer(prompt: str) -> str:
        q_match = re.search(r"QUESTION:\s*(.+)", prompt)
        question = q_match.group(1) if q_match else ""
        qtok = set(_WORD.findall(question.lower())) - {"the", "a", "of", "for", "is", "what", "how", "my", "in", "to"}
        best = (0, None, "")
        for m in _CHUNK_HDR.finditer(prompt):
            start = m.end()
            nxt = _CHUNK_HDR.search(prompt, start)
            body = prompt[start: nxt.start() if nxt else len(prompt)]
            for sent in re.split(r"(?<=[.!?])\s+", body):
                overlap = len(qtok & set(_WORD.findall(sent.lower())))
                if overlap > best[0]:
                    best = (overlap, m.group("id"), sent.strip())
        if best[1] is None or best[0] < 2:
            return json.dumps({"answer": "The provided documents do not contain this information.",
                               "sources": [], "confidence": 0.1, "answerable": False,
                               "reasoning": "No supporting passage found."})
        return json.dumps({"answer": best[2], "sources": [best[1]], "confidence": 0.8, "answerable": True,
                           "reasoning": "Extracted from the best-matching passage."})


def get_chat_model(model: str, json_schema: dict | None = None) -> BaseChatModel:
    s = get_settings()
    if s.provider == "fake":
        return FakeChatModel()
    from langchain_ollama import ChatOllama

    fmt: Any = json_schema if (json_schema and s.constrained_json) else ("json" if json_schema else None)
    return ChatOllama(
        model=model,
        base_url=s.ollama_base_url,
        temperature=s.llm_temperature,
        num_ctx=s.llm_num_ctx,
        num_predict=s.llm_max_tokens,
        format=fmt,
        keep_alive="30m",
        client_kwargs={"timeout": s.llm_timeout_s},
    )


def usage_from_message(msg: AIMessage) -> tuple[int, int]:
    """(input_tokens, output_tokens) from a LangChain AIMessage, tolerant of provider differences."""
    um = getattr(msg, "usage_metadata", None) or {}
    if um:
        return int(um.get("input_tokens", 0)), int(um.get("output_tokens", 0))
    rm = getattr(msg, "response_metadata", None) or {}
    return int(rm.get("prompt_eval_count", 0)), int(rm.get("eval_count", 0))
