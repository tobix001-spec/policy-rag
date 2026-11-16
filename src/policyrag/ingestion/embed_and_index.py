"""Build the FAISS index.

    python -m policyrag.ingestion.embed_and_index

Writes data/index/{index.faiss, chunks.jsonl, manifest.json} and data/processed/chunks.jsonl.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

from policyrag.config import get_settings
from policyrag.ingestion.chunking import Chunk, SemanticChunker
from policyrag.ingestion.load_docs import load_documents
from policyrag.providers import get_embedder, l2_normalize


def corpus_hash(raw_dir: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(raw_dir.rglob("*")):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def build_index(raw_dir: Path | None = None, index_dir: Path | None = None, semantic: bool = True) -> dict:
    s = get_settings()
    raw_dir = raw_dir or s.data_dir / "raw"
    index_dir = index_dir or s.index_dir
    index_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    docs = load_documents(raw_dir)
    embedder = get_embedder()
    chunker = SemanticChunker(embedder if semantic else None, s.chunk_breakpoint_percentile,
                              s.chunk_min_chars, s.chunk_max_chars, s.chunk_overlap_chars)
    chunks: list[Chunk] = chunker.chunk_documents(docs)
    t_chunk = time.perf_counter() - t0

    vecs = l2_normalize(embedder.embed_documents([c.embed_text for c in chunks]))
    index = faiss.IndexFlatIP(vecs.shape[1])  # inner product on unit vectors == cosine
    index.add(vecs)
    faiss.write_index(index, str(index_dir / "index.faiss"))
    np.save(index_dir / "vectors.npy", vecs)

    lines = "\n".join(json.dumps(c.to_dict()) for c in chunks) + "\n"
    (index_dir / "chunks.jsonl").write_text(lines, encoding="utf-8")
    processed = s.data_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    (processed / "chunks.jsonl").write_text(lines, encoding="utf-8")

    lengths = [len(c.text) for c in chunks]
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embedding_model": embedder.name, "dim": int(vecs.shape[1]), "index_type": "IndexFlatIP(normalized)",
        "n_docs": len(docs), "n_chunks": len(chunks), "corpus_hash": corpus_hash(raw_dir),
        "chunking": {"strategy": "semantic" if semantic else "recursive",
                     "breakpoint_percentile": s.chunk_breakpoint_percentile,
                     "min_chars": s.chunk_min_chars, "max_chars": s.chunk_max_chars},
        "chunk_chars": {"mean": float(np.mean(lengths)), "p50": float(np.median(lengths)),
                        "max": int(np.max(lengths))},
        "seconds": {"chunking": round(t_chunk, 2), "total": round(time.perf_counter() - t0, 2)},
    }
    (index_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recursive-only", action="store_true", help="skip semantic chunking (ablation)")
    args = ap.parse_args()
    print(json.dumps(build_index(semantic=not args.recursive_only), indent=2))


if __name__ == "__main__":
    main()
