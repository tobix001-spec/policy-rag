"""Human-in-the-loop review queue (SQLite). Optional webhook notification (e.g. Slack)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import httpx

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    question TEXT NOT NULL,
    response_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    reasons TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    resolution TEXT,
    resolved_by TEXT,
    resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_review_status ON review_items(status);
"""


class ReviewQueue:
    def __init__(self, db_path: Path, webhook_url: str | None = None):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.webhook_url = webhook_url or os.environ.get("POLICYRAG_REVIEW_WEBHOOK")
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def enqueue(self, question: str, response: dict, confidence: float, reasons: list[str]) -> int:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock, self._conn() as c:
            cur = c.execute(
                "INSERT INTO review_items(created_at, question, response_json, confidence, reasons) VALUES (?,?,?,?,?)",
                (now, question, json.dumps(response), confidence, json.dumps(reasons)))
            item_id = int(cur.lastrowid)
        if self.webhook_url:
            try:
                httpx.post(self.webhook_url, timeout=3, json={
                    "text": f"PolicyRAG review #{item_id} (confidence {confidence:.2f}, {', '.join(reasons)}): {question}"})
            except httpx.HTTPError:
                pass  # notification is best effort; the item is already persisted
        return item_id

    def list(self, status: str = "open", limit: int = 50) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM review_items WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["response"] = json.loads(d.pop("response_json"))
            d["reasons"] = json.loads(d["reasons"])
            out.append(d)
        return out

    def resolve(self, item_id: int, resolution: str, resolved_by: str = "reviewer") -> bool:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock, self._conn() as c:
            cur = c.execute("UPDATE review_items SET status='resolved', resolution=?, resolved_by=?, resolved_at=? "
                            "WHERE id=? AND status='open'", (resolution, resolved_by, now, item_id))
            return cur.rowcount == 1

    def counts(self) -> dict:
        with self._conn() as c:
            rows = c.execute("SELECT status, COUNT(*) n FROM review_items GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}
