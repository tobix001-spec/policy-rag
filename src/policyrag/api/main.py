"""FastAPI service.

    uvicorn policyrag.api.main:app --port 8000

Access scope comes from the `X-Role` header (customer -> public docs; staff -> public + internal).
In production this would be derived from the authenticated principal, never trusted from the client.
"""
from __future__ import annotations

import logging
import subprocess
import sys
import threading
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from policyrag.api.middleware import RequestContextMiddleware
from policyrag.api.schemas import EvalRequest, QueryRequest, QueryResponse, ResolveRequest
from policyrag.config import PROJECT_ROOT, get_settings
from policyrag.monitoring.metrics import REGISTRY, REVIEW_OPEN

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("policyrag")

ROLE_SCOPES = {"customer": ("public",), "staff": ("public", "internal")}
_state: dict = {}
_jobs: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    from policyrag.generation.generator import get_service

    svc = get_service()
    _state["service"] = svc
    if get_settings().provider != "fake":
        try:  # pay the CUDA/model cold start (~10-80s) at boot, not on the first user
            svc.answer("What is the late payment fee?", use_cache=False)
            log.info("warm-up complete")
        except Exception as e:  # noqa: BLE001
            log.warning("warm-up failed: %s", e)
    REVIEW_OPEN.set(svc.review.counts().get("open", 0))
    yield


app = FastAPI(title="PolicyRAG", version="0.1.0", lifespan=lifespan,
              description="RAG over Velmora Assurance policy, claims and support documents.")
app.add_middleware(RequestContextMiddleware)


def _svc():
    return _state["service"]


@app.post("/query", response_model=QueryResponse, response_model_exclude_none=True)
def query(req: QueryRequest, x_role: str = Header("customer")):
    from policyrag.retrieval.retriever import Filters

    scope = ROLE_SCOPES.get(x_role.lower())
    if scope is None:
        raise HTTPException(400, f"unknown role {x_role!r}; use one of {sorted(ROLE_SCOPES)}")
    flt = Filters(allowed_confidentiality=scope, doc_types=tuple(req.doc_types) if req.doc_types else None,
                  line=req.line)
    out = _svc().answer(req.question, flt, use_cache=req.use_cache)
    if not req.include_retrieved:
        out = {k: v for k, v in out.items() if k != "retrieved"}
    return out


@app.get("/health")
def health():
    s = get_settings()
    svc = _svc()
    info = {"status": "ok", "provider": s.provider, "index": {"n_chunks": len(svc.retriever.chunks),
                                                              "n_docs": svc.retriever.manifest["n_docs"],
                                                              "built_at": svc.retriever.manifest["built_at"],
                                                              "embedding_model": svc.retriever.manifest["embedding_model"]}}
    if s.provider != "fake":
        try:
            tags = httpx.get(f"{s.ollama_base_url}/api/tags", timeout=2).json()
            have = {m["name"] for m in tags.get("models", [])}
            info["llm"] = {"ollama": "up", "models": {m: (m in have) for m in {s.llm_default, s.llm_small}}}
            if not all(info["llm"]["models"].values()):
                info["status"] = "degraded"
        except httpx.HTTPError:
            info["llm"] = {"ollama": "down"}
            info["status"] = "degraded"
    return info


@app.get("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics/summary")
def metrics_summary():
    svc = _svc()
    return {**svc.log.summary(), "cache": svc.cache.stats() if svc.cache else None, "review_queue": svc.review.counts()}


@app.get("/review")
def review_list(status: str = "open", limit: int = 50):
    return _svc().review.list(status, limit)


@app.post("/review/{item_id}/resolve")
def review_resolve(item_id: int, req: ResolveRequest):
    if not _svc().review.resolve(item_id, req.resolution, req.resolved_by):
        raise HTTPException(404, "no open review item with that id")
    REVIEW_OPEN.set(_svc().review.counts().get("open", 0))
    return {"resolved": item_id}


@app.post("/cache/clear")
def cache_clear():
    if _svc().cache:
        _svc().cache.clear()
    return {"cleared": True}


# ---------------------------------------------------------------- evaluation jobs
def _run_eval(job_id: str, req: EvalRequest) -> None:
    cmd = [sys.executable, "-m", "policyrag.evaluation.evaluate", "--name", req.name, "--limit", str(req.limit)]
    if not req.judge:
        cmd.append("--no-judge")
    if req.gate:
        cmd.append("--gate")
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    _jobs[job_id].update(status="passed" if proc.returncode == 0 else "failed", returncode=proc.returncode,
                         tail=proc.stdout.splitlines()[-25:], report=f"reports/eval_{req.name}.json")


@app.post("/evaluate", status_code=202)
def evaluate(req: EvalRequest):
    """Runs the golden-set eval in a subprocess (isolated settings, no cache) and returns a job id."""
    if any(j["status"] == "running" for j in _jobs.values()):
        raise HTTPException(409, "an evaluation is already running")
    job_id = uuid.uuid4().hex[:8]
    _jobs[job_id] = {"status": "running", "request": req.model_dump()}
    threading.Thread(target=_run_eval, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id, "status_url": f"/evaluate/{job_id}"}


@app.get("/evaluate/{job_id}")
def evaluate_status(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(404, "unknown job")
    return _jobs[job_id]
