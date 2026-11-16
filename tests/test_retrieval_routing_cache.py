import numpy as np

from policyrag.generation.cache import EntitySignature, SemanticCache
from policyrag.generation.router import route
from policyrag.retrieval.retriever import Filters


def test_public_queries_never_see_internal_chunks(retriever):
    res = retriever.retrieve("large-loss referral threshold senior adjuster", Filters(("public",)))
    assert res.hits and all(h.chunk["confidentiality"] == "public" for h in res.hits)
    staff = retriever.retrieve("large-loss referral threshold senior adjuster", Filters(("public", "internal")))
    assert any(h.chunk["confidentiality"] == "internal" for h in staff.hits)


def test_hybrid_finds_the_named_product(retriever):
    res = retriever.retrieve("What is the comprehensive deductible on Classic Car?")
    assert any(h.chunk["product"] == "Classic Car" for h in res.hits[:3])


def test_amendment_expansion_pulls_in_superseding_doc(retriever):
    base_doc, amend_ids = next(iter(retriever.amendments.items()))
    product = next(c["product"] for c in retriever.chunks if c["doc_id"] == base_doc)
    res = retriever.retrieve(f"{product} policy document overview coverage", Filters(("public",)))
    if any(h.chunk["doc_id"] == base_doc for h in res.hits):
        ids = {h.chunk["doc_id"] for h in res.hits}
        assert ids & {retriever.chunks[i]["doc_id"] for i in amend_ids}


def test_doc_type_and_line_filters(retriever):
    res = retriever.retrieve("how do I file a claim", Filters(("public",), doc_types=("claims",), line="pet"))
    assert res.hits and all(h.chunk["doc_type"] == "claims" and h.chunk["line"] == "pet" for h in res.hits)


def test_router():
    assert route("What is the ER copay for Gold PPO?").name == "simple"
    assert route("Which has the lower deductible: Gold PPO or Silver PPO?").name == "complex"
    assert route("Why was my claim denied?").name == "complex"


def _unit(seed):
    v = np.random.default_rng(seed).normal(size=8).astype("float32")
    return v / np.linalg.norm(v)


def test_cache_entity_guard_blocks_sibling_products():
    sig = EntitySignature(["Gold PPO", "Silver PPO"])
    cache = SemanticCache(sig, threshold=0.0, ttl_s=60, max_entries=10)
    v = _unit(1)
    cache.put("What is the deductible for Gold PPO?", v, "k", {"answer": "$500"})
    assert cache.get("What is the deductible for Gold PPO?", v, "k")[0]["answer"] == "$500"
    # identical vector (worst case for embeddings), different product -> must miss
    assert cache.get("What is the deductible for Silver PPO?", v, "k") is None
    # same question under a different access scope -> must miss
    assert cache.get("What is the deductible for Gold PPO?", v, "other-scope") is None
    assert cache.guard_rejections >= 2


def test_cache_threshold_and_ttl():
    sig = EntitySignature([])
    cache = SemanticCache(sig, threshold=0.99, ttl_s=60, max_entries=10)
    cache.put("late fee amount", _unit(1), "k", {"answer": "$15"})
    assert cache.get("late fee amount", _unit(2), "k") is None  # dissimilar vector
    cache.ttl = -1
    assert cache.get("late fee amount", _unit(1), "k") is None  # expired
