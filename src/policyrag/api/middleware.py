"""Request-id propagation, structured access logs, and a last-resort error handler."""
from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from policyrag.monitoring.metrics import ERRORS

log = logging.getLogger("policyrag.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as e:  # noqa: BLE001
            ERRORS.labels("unhandled").inc()
            log.exception("unhandled error rid=%s", rid)
            response = JSONResponse({"error": "internal_error", "detail": type(e).__name__, "request_id": rid},
                                    status_code=500)
        ms = (time.perf_counter() - t0) * 1000
        response.headers["x-request-id"] = rid
        response.headers["x-response-time-ms"] = f"{ms:.1f}"
        log.info(json.dumps({"rid": rid, "method": request.method, "path": request.url.path,
                             "status": response.status_code, "ms": round(ms, 1)}))
        return response
