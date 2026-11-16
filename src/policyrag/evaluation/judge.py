"""LLM-as-judge metrics, implemented RAGAS-style against a local judge model.

faithfulness      = supported claims / total claims in the answer (claims checked against the context)
answer_relevancy  = mean cosine(original question, questions the judge generates from the answer)

Caveat worth stating in any report: the judge (qwen2.5:7b) is also the generator for complex
queries, so self-preference bias is possible. Deterministic metrics (fact match, retrieval
recall) are the primary signal; judge metrics are secondary.
"""
from __future__ import annotations

import json
import re

import numpy as np
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from policyrag.config import get_settings
from policyrag.providers import get_chat_model, get_embedder, usage_from_message


class Claim(BaseModel):
    claim: str
    supported: bool


class FaithfulnessVerdict(BaseModel):
    claims: list[Claim]


class GeneratedQuestions(BaseModel):
    questions: list[str]


FAITH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "JUDGE_TASK: faithfulness. You are a strict fact checker."),
    ("human", "CONTEXT:\n{context}\n\nANSWER:\n{answer}\n\n"
              "Break the ANSWER into its atomic factual claims (numbers, conditions, product names). For each claim, "
              "set supported=true only if the CONTEXT states it directly. Return JSON: "
              '{{"claims": [{{"claim": "...", "supported": true}}]}}'),
])

RELEVANCY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "JUDGE_TASK: question generation."),
    ("human", "ANSWER:\n{answer}\n\nWrite 3 different questions that this ANSWER directly answers. "
              'Return JSON: {{"questions": ["...", "...", "..."]}}'),
])

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


class Judge:
    def __init__(self):
        s = get_settings()
        self.faith_llm = get_chat_model(s.judge_model, FaithfulnessVerdict.model_json_schema())
        self.q_llm = get_chat_model(s.judge_model, GeneratedQuestions.model_json_schema())
        self.embedder = get_embedder()
        self.tokens = [0, 0]

    def _call(self, chain, inputs: dict, model_cls):
        msg = chain.invoke(inputs)
        i, o = usage_from_message(msg)
        self.tokens[0] += i
        self.tokens[1] += o
        return model_cls.model_validate_json(_FENCE.sub("", str(msg.content).strip()))

    def faithfulness(self, context: str, answer: str) -> tuple[float | None, list[dict]]:
        try:
            v = self._call(FAITH_PROMPT | self.faith_llm, {"context": context, "answer": answer}, FaithfulnessVerdict)
        except Exception:  # noqa: BLE001 - a judge failure is recorded as missing, not as 0
            return None, []
        if not v.claims:
            return None, []
        return sum(c.supported for c in v.claims) / len(v.claims), [c.model_dump() for c in v.claims]

    def answer_relevancy(self, question: str, answer: str) -> float | None:
        try:
            g = self._call(RELEVANCY_PROMPT | self.q_llm, {"answer": answer}, GeneratedQuestions)
        except Exception:  # noqa: BLE001
            return None
        qs = [q for q in g.questions if q.strip()][:3]
        if not qs:
            return None
        vecs = self.embedder.embed_documents([question] + qs)
        return float(np.mean(vecs[1:] @ vecs[0]))


def dumps(x) -> str:
    return json.dumps(x, ensure_ascii=False)
