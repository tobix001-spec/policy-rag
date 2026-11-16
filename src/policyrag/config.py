"""Central configuration. Every knob is overridable with a POLICYRAG_* env var (or .env)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ModelPrice(BaseModel):
    """USD per 1M tokens. For local models this is an *API-equivalent estimate*,
    i.e. what the same token volume would cost on a comparable hosted model."""

    input_per_m: float
    output_per_m: float
    reference: str = ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POLICYRAG_", env_file=".env", extra="ignore")

    # --- paths -------------------------------------------------------------
    data_dir: Path = PROJECT_ROOT / "data"
    index_dir: Path = PROJECT_ROOT / "data" / "index"
    log_dir: Path = PROJECT_ROOT / "logs"
    reports_dir: Path = PROJECT_ROOT / "reports"

    # --- providers ---------------------------------------------------------
    # "local" = sentence-transformers + Ollama; "fake" = deterministic offline stubs (tests/CI)
    provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # bge v1.5 recommends this instruction on queries only (not passages)
    embedding_query_instruction: str = "Represent this sentence for searching relevant passages: "
    reranker_model: str = "BAAI/bge-reranker-base"
    device: str = "auto"  # auto | cuda | cpu

    ollama_base_url: str = "http://localhost:11434"
    llm_default: str = "qwen2.5:7b"   # complex queries
    llm_small: str = "qwen2.5:3b"     # simple factual queries (cost routing)
    judge_model: str = "qwen2.5:7b"   # LLM-as-judge for faithfulness/relevancy
    llm_temperature: float = 0.0
    llm_num_ctx: int = 8192
    llm_timeout_s: float = 120.0
    # Hard cap on generated tokens. Eval v3 caught a runaway generation (one 3b answer looped for 16 min
    # and doubled the run's cost); normal answers use ~100-200 tokens.
    llm_max_tokens: int = 512
    constrained_json: bool = True     # pass the JSON schema to Ollama's structured output

    # --- chunking ----------------------------------------------------------
    chunk_breakpoint_percentile: float = 85.0
    chunk_min_chars: int = 200
    chunk_max_chars: int = 1200
    chunk_overlap_chars: int = 120

    # --- retrieval ---------------------------------------------------------
    dense_k: int = 20
    bm25_k: int = 20
    hybrid: bool = True
    rrf_k: int = 60
    rerank: bool = True
    final_k: int = 5
    expand_amendments: bool = True
    decompose_multi_entity: bool = True   # one sub-retrieval per product named in the question
    decompose_per_product_k: int = 4      # chunks kept per product in a decomposed retrieval
    entity_filter: bool = True            # single-product question: other products' chunks rank last
    # Listing amendments first in the context was tried in v2 and measured WORSE on amendment questions
    # (86.7% vs 100% in a 15-case probe), so context keeps plain rerank order. Kept as a flag for ablation.
    amendments_first: bool = False
    grounding_check: bool = True          # numbers/products in the answer must appear in cited chunks
    context_routing: bool = True          # upgrade to the default model when an amendment is in play

    # --- generation / confidence --------------------------------------------
    confidence_threshold: float = 0.55
    confidence_w_retrieval: float = 0.5
    confidence_w_llm: float = 0.5
    max_json_repairs: int = 1

    # --- cache ---------------------------------------------------------------
    cache_enabled: bool = True
    cache_backend: str = "memory"  # memory | redis
    cache_similarity: float = 0.97
    cache_ttl_s: int = 3600
    cache_max_entries: int = 2000
    redis_url: str = "redis://localhost:6379/0"

    # --- pricing (API-equivalent estimates; edit to taste) -------------------
    prices: dict[str, ModelPrice] = Field(
        default_factory=lambda: {
            "qwen2.5:7b": ModelPrice(input_per_m=0.15, output_per_m=0.60, reference="gpt-4o-mini list price"),
            "qwen2.5:3b": ModelPrice(input_per_m=0.10, output_per_m=0.40, reference="gpt-4.1-nano list price"),
            "fake-llm": ModelPrice(input_per_m=0.0, output_per_m=0.0),
        }
    )

    @property
    def review_db(self) -> Path:
        return self.data_dir / "review_queue.sqlite"


@lru_cache
def get_settings() -> Settings:
    return Settings()
