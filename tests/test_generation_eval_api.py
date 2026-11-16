import json

import pytest

from policyrag.evaluation.evaluate import run_gate, score_case, summarize
from policyrag.evaluation.golden_set import load_golden
from policyrag.generation.generator import AnswerService, coerce
from policyrag.generation.review_queue import ReviewQueue
from policyrag.monitoring.metrics import QueryLog
from policyrag.retrieval.retriever import Filters


@pytest.fixture
def service(retriever, tmp_path):
    return AnswerService(retriever=retriever, review=ReviewQueue(tmp_path / "rq.sqlite"),
                         log=QueryLog(tmp_path / "q.jsonl"))


def test_coerce_percent_confidence():
    fixed, fixes = coerce('{"answer": "x", "answerable": true, "sources": "a#c0", "confidence": 99, "reasoning": "r"}')
    d = json.loads(fixed)
    assert d["confidence"] == 0.99 and d["sources"] == ["a#c0"]
    assert set(fixes) == {"confidence_percent_to_fraction", "sources_str_to_list"}


def test_grounding_verifier():
    from policyrag.generation.generator import grounding_issues

    ctx = ["Fleet Commercial — Claims Guide\nAppeals must be received within 30 days after the denial."]
    assert grounding_issues("appeal deadline Fleet Commercial?", "30 days", ctx, ["Fleet Commercial"]) == []
    assert grounding_issues("appeal deadline Fleet Commercial?", "120 days", ctx, ["Fleet Commercial"]) == \
        ["ungrounded_number"]
    assert "product_not_in_sources" in grounding_issues("x", "30 days", ctx, ["Fleet Commercial", "Classic Car"])
    # numbers echoed from the question are not hallucinations
    assert grounding_issues("claims in 12 months?", "30 days within 12 months", ctx, []) == []


def test_multi_entity_decomposition_covers_both_products(retriever):
    q = "Which has the higher annual benefit limit: Senior Pet or Pet Wellness?"
    assert retriever.products_in(q) == ["Senior Pet", "Pet Wellness"]
    res = retriever.retrieve(q)
    products = {h.chunk["product"] for h in res.hits}
    assert {"Senior Pet", "Pet Wellness"} <= products


def test_answer_contract(service):
    out = service.answer("What is the late payment fee?", use_cache=False)
    assert out["schema_version"] == "PolicyAnswer.v1"
    assert out["format"]["valid"] and out["format"]["valid_first_try"]
    assert out["status"] in ("answered", "needs_review")
    retrieved = {h["chunk_id"] for h in out["retrieved"]}
    assert all(s["chunk_id"] in retrieved for s in out["sources"])
    assert out["usage"]["input_tokens"] > 0 and out["latency_ms"]["total"] > 0


def test_invalid_output_goes_to_review(service, monkeypatch):
    from langchain_core.messages import AIMessage

    monkeypatch.setattr(service, "_invoke", lambda *a, **k: (AIMessage(content="not json at all"), "fake-llm", False))
    service.s.max_json_repairs = 0
    try:
        out = service.answer("What is the late payment fee?", use_cache=False)
    finally:
        service.s.max_json_repairs = 1
    assert out["status"] == "needs_review" and "invalid_output" in out["review_reasons"]
    assert out["review_id"] is not None
    item = service.review.list()[0]
    assert item["id"] == out["review_id"]
    assert service.review.resolve(item["id"], "Late fee is $15.")
    assert service.review.counts().get("resolved") == 1


def test_invalid_small_model_output_escalates_to_default_model(service, monkeypatch):
    from langchain_core.messages import AIMessage

    good = AIMessage(content=json.dumps({"reasoning": "r", "answer": "The late fee is $15.", "answerable": True,
                                         "sources": [], "confidence": 0.9}))
    calls = []

    def fake_invoke(model, context, question):
        calls.append(model)
        if model == service.s.llm_small:
            return AIMessage(content='{"reasoning": "rambling with no end'), model, False  # truncated JSON
        return good, model, False

    monkeypatch.setattr(service, "_invoke", fake_invoke)
    service.s.max_json_repairs = 0
    try:
        out = service.answer("What is the late payment fee?", use_cache=False, force_route="simple")
    finally:
        service.s.max_json_repairs = 1
    assert calls == [service.s.llm_small, service.s.llm_default]
    assert out["route"]["escalated"] and out["format"]["valid"] and "invalid_output" not in out["review_reasons"]


def test_llm_outage_degrades_gracefully(service, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("ollama down")

    monkeypatch.setattr(service, "_invoke", boom)
    out = service.answer("What is the late payment fee?", use_cache=False)
    assert out["status"] == "needs_review" and out["answer"]


def test_cache_hit_on_repeat(service):
    q = "How long is a password reset link valid?"
    first = service.answer(q)
    second = service.answer(q)
    if first["status"] == "answered":
        assert second["cache"]["hit"] and second["usage"]["cost_usd_estimate"] == 0


def test_comparison_grader_checks_the_winner():
    from policyrag.evaluation.evaluate import comparison_winner_ok

    q = "Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower?"
    exp = "Silver PPO (Bronze HMO: 30%; Silver PPO: 10%)."
    assert comparison_winner_ok("Silver PPO has the lower rate: 10% versus 30% for Bronze HMO.", exp, q)
    assert not comparison_winner_ok("Bronze HMO has a lower rate: 30% for Bronze HMO versus 10% for Silver PPO.", exp, q)
    assert not comparison_winner_ok("Both Bronze HMO and Silver PPO have the same rate of 30%.", exp, q)
    # cases from the v1 audit: conclusion stated last, after both values
    assert comparison_winner_ok("Pet Wellness has a 20 days grace period, while Exotic Pet has a 60 days grace "
                                "period. Exotic Pet has the longer grace period.",
                                "Exotic Pet (Pet Wellness: 20 days; Exotic Pet: 60 days).",
                                "Which has the longer premium grace period: Pet Wellness or Exotic Pet?")
    # opposite comparative: "Term 30 is faster" answers "which is slower?" with Universal Life
    assert comparison_winner_ok("Term 30 has a faster claim decision time: 10 days for Term 30 versus 14 days.",
                                "Universal Life (Term 30: 10 days; Universal Life: 14 days).",
                                "Which has the slower claim decision time: Term 30 or Universal Life?")
    # v2 audit: values first, conclusion in a ", so ..." clause of the same sentence
    assert comparison_winner_ok("The water backup sublimit is $7,500 for Condo Shield and $25,000 for HomeBasic, "
                                "so HomeBasic has the higher water backup sublimit.",
                                "HomeBasic (Condo Shield: $7,500; HomeBasic: $25,000).",
                                "Which has the higher water backup sublimit: Condo Shield or HomeBasic?")
    assert not comparison_winner_ok("The sublimit is $7,500 for Condo Shield and $25,000 for HomeBasic, "
                                    "so Condo Shield has the higher sublimit.",
                                    "HomeBasic (Condo Shield: $7,500; HomeBasic: $25,000).",
                                    "Which has the higher water backup sublimit: Condo Shield or HomeBasic?")
    # values without a conclusion do not answer "which"
    assert not comparison_winner_ok("Rideshare Auto has a 30-day grace period, while Basic Liability has a 20-day "
                                    "grace period.", "Basic Liability (Rideshare Auto: 30 days; Basic Liability: 20 days).",
                                    "Which has the shorter premium grace period: Rideshare Auto or Basic Liability?")


def test_scoring_and_gate(built, service):
    cases = load_golden()[:12] + [c for c in load_golden() if c.type == "unanswerable"][:3]
    rows = [score_case(c, service.answer(c.question, Filters(tuple(c.allowed_confidentiality)), use_cache=False))
            for c in cases]
    s = summarize(rows)
    assert 0 <= s["answer_accuracy"] <= 1 and s["internal_leaks"] == 0
    ok, checks = run_gate(s, s, {"floors": {"answer_accuracy": 0.0}, "max_drop": {"answer_accuracy": 0.0},
                                 "ceilings": {"internal_leaks": 0}})
    assert ok and len(checks) == 3
    worse = {**s, "answer_accuracy": s["answer_accuracy"] - 0.2}
    ok, checks = run_gate(worse, s, {"max_drop": {"answer_accuracy": 0.05}})
    assert not ok


def test_api_end_to_end(built):
    from fastapi.testclient import TestClient

    from policyrag.api.main import app

    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        r = client.post("/query", json={"question": "What is the large-loss referral threshold for auto claims?",
                                        "include_retrieved": True})
        assert r.status_code == 200
        assert all(not h["chunk_id"].startswith("internal-") for h in r.json()["retrieved"])
        r = client.post("/query", headers={"X-Role": "staff"},
                        json={"question": "What is the large-loss referral threshold for auto claims?",
                              "include_retrieved": True})
        assert any(h["chunk_id"].startswith("internal-") for h in r.json()["retrieved"])
        assert client.post("/query", headers={"X-Role": "admin"}, json={"question": "hello there"}).status_code == 400
        assert "policyrag_queries_total" in client.get("/metrics").text
        assert "latency_ms_p95" in client.get("/metrics/summary").json()
        assert isinstance(client.get("/review").json(), list)
