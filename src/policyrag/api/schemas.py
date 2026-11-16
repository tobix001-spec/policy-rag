"""API request/response models."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    doc_types: list[Literal["policy", "claims", "support"]] | None = None
    line: Literal["health", "auto", "home", "travel", "pet", "life"] | None = None
    use_cache: bool = True
    include_retrieved: bool = Field(False, description="Return every retrieved chunk with its scores")


class Source(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    section: str
    last_updated: str
    snippet: str
    rerank_score: float | None = None


class Confidence(BaseModel):
    final: float
    retrieval: float
    llm: float
    threshold: float


class RouteInfo(BaseModel):
    name: str
    model: str
    reasons: list[str]
    fallback_used: bool
    escalated: bool = False


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd_estimate: float = Field(description="API-equivalent estimate; local inference has no per-token bill")


class QueryResponse(BaseModel):
    request_id: str
    schema_version: str
    question: str
    answer: str
    answerable: bool
    reasoning: str
    sources: list[Source]
    confidence: Confidence
    status: Literal["answered", "needs_review"]
    review_reasons: list[str]
    review_id: int | None
    route: RouteInfo
    usage: Usage
    latency_ms: dict[str, float]
    cache: dict
    format: dict
    retrieved: list[dict] | None = None


class ResolveRequest(BaseModel):
    resolution: str = Field(min_length=1, max_length=4000)
    resolved_by: str = "reviewer"


class EvalRequest(BaseModel):
    name: str = Field("api", pattern=r"^[a-zA-Z0-9_-]{1,40}$")
    limit: int = Field(20, ge=1, le=500)
    judge: bool = False
    gate: bool = True
