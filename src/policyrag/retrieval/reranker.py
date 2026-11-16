"""Cross-encoder reranking (BAAI/bge-reranker-base by default)."""
from __future__ import annotations

import numpy as np

from policyrag.providers import get_reranker


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def rerank_scores(query: str, passages: list[str]) -> np.ndarray:
    """Calibrated-ish relevance in [0, 1] (sigmoid of cross-encoder logits)."""
    return sigmoid(get_reranker().score(query, passages))
