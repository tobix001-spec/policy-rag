import json

from policyrag.ingestion.chunking import SemanticChunker, split_sections
from policyrag.ingestion.load_docs import RawDoc, load_documents
from policyrag.providers import FakeEmbedder
from policyrag.textnorm import contains_any, norm


def test_golden_set_shape(built):
    golden = json.loads((built["data"] / "golden_set.json").read_text(encoding="utf-8"))
    assert len(golden) == 180
    types = {c["type"] for c in golden}
    assert types == {"simple", "amendment", "comparison", "internal", "unanswerable"}
    assert len({c["id"] for c in golden}) == 180
    for c in golden:
        assert c["answerable"] == (c["type"] != "unanswerable")
        if c["answerable"]:
            assert c["must_contain"] and c["relevant_doc_ids"]


def test_every_fact_is_stated_in_its_documents(built):
    """The golden set is only trustworthy if each fact literally appears where the registry says."""
    facts = json.loads((built["data"] / "facts.json").read_text(encoding="utf-8"))
    docs = {d.doc_id: d.text for d in load_documents(built["data"] / "raw")}
    for f in facts:
        for doc_id in f["doc_ids"]:
            assert contains_any(docs[doc_id], f["match"]), (f["fact_id"], doc_id)


def test_amended_facts_point_only_to_amendments(built):
    facts = {f["fact_id"]: f for f in json.loads((built["data"] / "facts.json").read_text(encoding="utf-8"))}
    amended = [f for f in facts.values() if f["fact_id"].endswith("@amended")]
    assert len(amended) == 18
    for f in amended:
        assert all(d.startswith("amendment-") for d in f["doc_ids"])
        base = facts[f["fact_id"].removesuffix("@amended")]
        assert base["superseded_by"] == f["fact_id"] and base["value"] != f["value"]


def test_norm_handles_money_formats():
    assert norm("$1,500") == "$1500"
    assert contains_any("The deductible is $1,500 per year", ["$1500"])
    assert not contains_any("The deductible is $15,000", ["$1500"])
    assert not contains_any("File within 120 days", ["20 days"])
    assert contains_any("File within 20 days.", ["20 days"])
    assert contains_any("costs $1,500.", ["$1500"])


def test_sections_and_chunk_limits():
    text = "# Title\n\n## A\n\nShort.\n\n## B\n\n" + " ".join(f"Sentence number {i} is here." for i in range(120))
    assert [h for h, _ in split_sections(text)] == ["A", "B"]
    chunker = SemanticChunker(FakeEmbedder(), min_chars=200, max_chars=500, overlap_chars=50)
    chunks = chunker.chunk_documents([RawDoc("d1", text, "d1.md", {"title": "T"})])
    assert all(len(c.text) <= 500 for c in chunks)
    # the undersized section A is merged forward instead of becoming its own chunk
    assert chunks[0].section == "A / B" and "Short." in chunks[0].text
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert all(c.embed_text.startswith("T | ") for c in chunks)


def test_index_manifest(built):
    m = built["manifest"]
    assert m["n_docs"] == 189 and m["n_chunks"] > 300
    assert m["embedding_model"] == "fake-embedder"
