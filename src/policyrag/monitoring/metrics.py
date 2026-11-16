"""Prometheus metrics + structured JSONL query log + rolling latency percentiles."""
from __future__ import annotations

import json
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from policyrag.config import get_settings

REGISTRY = CollectorRegistry()

QUERIES = Counter("policyrag_queries_total", "Queries served", ["route", "status", "cache"], registry=REGISTRY)
LATENCY = Histogram("policyrag_query_latency_seconds", "End-to-end query latency", ["route"], registry=REGISTRY,
                    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 8, 13, 21, 34))
STAGE = Histogram("policyrag_stage_latency_seconds", "Per-stage latency", ["stage"], registry=REGISTRY,
                  buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10))
TOKENS = Counter("policyrag_tokens_total", "LLM tokens", ["model", "kind"], registry=REGISTRY)
COST = Counter("policyrag_cost_usd_total", "Estimated API-equivalent cost (USD)", ["model"], registry=REGISTRY)
ERRORS = Counter("policyrag_errors_total", "Errors by type", ["type"], registry=REGISTRY)
FALLBACKS = Counter("policyrag_fallbacks_total", "Primary model failed, fallback used", registry=REGISTRY)
JSON_REPAIRS = Counter("policyrag_json_repairs_total", "Outputs that needed a JSON repair pass", ["outcome"], registry=REGISTRY)
REVIEW_OPEN = Gauge("policyrag_review_queue_open", "Open review items", registry=REGISTRY)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = get_settings().prices.get(model)
    if not price:
        return 0.0
    return input_tokens / 1e6 * price.input_per_m + output_tokens / 1e6 * price.output_per_m


class QueryLog:
    """Append-only JSONL log plus an in-memory window for p50/p95."""

    def __init__(self, path: Path | None = None, window: int = 2000):
        self.path = path or get_settings().log_dir / "queries.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lat: deque[float] = deque(maxlen=window)
        self._cost: deque[float] = deque(maxlen=window)
        self._lock = threading.Lock()

    def record(self, event: dict) -> None:
        event = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), **event}
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, default=str) + "\n")
            self._lat.append(float(event.get("latency_ms", 0)))
            self._cost.append(float(event.get("cost_usd", 0)))

    def summary(self) -> dict:
        with self._lock:
            lat = np.array(self._lat) if self._lat else np.zeros(1)
            cost = np.array(self._cost) if self._cost else np.zeros(1)
            n = len(self._lat)
        return {"window_queries": n, "latency_ms_p50": round(float(np.percentile(lat, 50)), 1),
                "latency_ms_p95": round(float(np.percentile(lat, 95)), 1),
                "cost_usd_per_query_mean": float(cost.mean()), "cost_usd_window_total": float(cost.sum())}
