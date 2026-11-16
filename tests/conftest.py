"""Tests run fully offline: fake embedder/reranker/LLM, a freshly generated corpus in a temp dir."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="policyrag-test-"))
os.environ["POLICYRAG_PROVIDER"] = "fake"
os.environ["POLICYRAG_DATA_DIR"] = str(_TMP / "data")
os.environ["POLICYRAG_INDEX_DIR"] = str(_TMP / "data" / "index")
os.environ["POLICYRAG_LOG_DIR"] = str(_TMP / "logs")
os.environ["POLICYRAG_REPORTS_DIR"] = str(_TMP / "reports")

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Generate the corpus + golden set and build the index once per test session."""
    import sys

    from policyrag.corpus import generate
    from policyrag.ingestion.embed_and_index import build_index

    argv = sys.argv
    sys.argv = ["generate", "--seed", "42"]
    try:
        generate.main()
    finally:
        sys.argv = argv
    manifest = build_index()
    return {"data": _TMP / "data", "manifest": manifest}


@pytest.fixture(scope="session")
def retriever(built):
    from policyrag.retrieval.retriever import get_retriever

    return get_retriever()
