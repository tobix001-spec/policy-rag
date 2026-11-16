"""PolicyRAG demo UI.   streamlit run ui/app.py"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st

API = os.environ.get("POLICYRAG_API_URL", "http://localhost:8000")
REPORTS = Path(__file__).resolve().parents[1] / "reports"
SAMPLES = [
    "What is the annual deductible for the Gold PPO plan?",
    "Which has the lower collision deductible: Classic Car or Premier Auto?",
    "What is the maximum file size for uploads in the mobile app?",
    "How long do I have to appeal a denied Fleet Commercial claim?",
    "What is the large-loss referral threshold for auto claims?",
    "What is the deductible for the Diamond PPO plan?",
]

st.set_page_config(page_title="PolicyRAG", layout="wide")


def api(method: str, path: str, **kw):
    try:
        r = httpx.request(method, f"{API}{path}", timeout=180, **kw)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        st.error(f"API error on {path}: {e}")
        return None


with st.sidebar:
    st.title("PolicyRAG")
    st.caption("Velmora Assurance policy · claims · support assistant")
    role = st.radio("Role", ["customer", "staff"], help="staff can retrieve INTERNAL adjuster documents")
    line = st.selectbox("Line of business", ["(any)", "health", "auto", "home", "travel", "pet", "life"])
    doc_types = st.multiselect("Document types", ["policy", "claims", "support"])
    use_cache = st.checkbox("Use semantic cache", value=True)
    health = api("GET", "/health")
    if health:
        st.success(f"API {health['status']} · {health['index']['n_chunks']} chunks / {health['index']['n_docs']} docs")

tab_ask, tab_review, tab_eval, tab_mon = st.tabs(["Ask", "Review queue", "Evaluation", "Monitoring"])

with tab_ask:
    pick = st.selectbox("Try a sample question", ["(type your own)"] + SAMPLES)
    question = st.text_input("Question", value="" if pick.startswith("(") else pick)
    if st.button("Ask", type="primary", disabled=len(question) < 3):
        body = {"question": question, "use_cache": use_cache, "include_retrieved": True,
                "line": None if line == "(any)" else line, "doc_types": doc_types or None}
        with st.spinner("Retrieving and generating…"):
            res = api("POST", "/query", json=body, headers={"X-Role": role})
        if res:
            if res["status"] == "answered":
                st.success("Answered")
                st.markdown(f"### {res['answer']}")
            else:
                st.warning(f"Held for human review (#{res['review_id']}): {', '.join(res['review_reasons'])}. "
                           "In production this draft is not shown to customers.")
                st.markdown(f"### ~~{res['answer']}~~" if res["answerable"] else f"### {res['answer']}")
                if res["answerable"]:
                    st.caption("Draft answer withheld: it failed verification.")
            st.caption(res["reasoning"])

            c = st.columns(6)
            c[0].metric("Confidence", f"{res['confidence']['final']:.2f}",
                        help=f"retrieval {res['confidence']['retrieval']:.2f} · llm {res['confidence']['llm']:.2f}")
            c[1].metric("Route", res["route"]["name"], help=", ".join(res["route"]["reasons"]))
            model = res["route"]["model"].split(":")[-1]  # "qwen2.5:7b" -> "7b"
            c[2].metric("Model", model + (" ↑" if res["route"].get("escalated") else ""), help=res["route"]["model"])
            c[3].metric("Latency", f"{res['latency_ms']['total']:.0f} ms")
            c[4].metric("Tokens", f"{res['usage']['input_tokens']}+{res['usage']['output_tokens']}")
            c[5].metric("Est. $ / 1k q", f"${res['usage']['cost_usd_estimate'] * 1000:.2f}",
                        help="API-equivalent estimate scaled to 1,000 such queries; local inference has no per-token bill")
            if res["cache"].get("hit"):
                st.info(f"Semantic cache hit (similarity {res['cache']['similarity']}) for: "
                        f"“{res['cache']['original_question']}”")

            st.subheader("Sources")
            for s in res["sources"]:
                with st.expander(f"{s['title']} — {s['section']}  ·  `{s['chunk_id']}`"):
                    st.write(s["snippet"])
                    st.caption(f"updated {s['last_updated']} · rerank {s['rerank_score']}")
            if res.get("retrieved"):
                st.subheader("Retrieved context")
                st.dataframe(pd.DataFrame([{"chunk_id": h["chunk_id"], "type": h["doc_type"],
                                            "rerank": h["scores"]["rerank"], "dense": h["scores"]["dense"],
                                            "bm25": h["scores"]["bm25"], "expanded": h["expanded"],
                                            "text": h["text"][:140]} for h in res["retrieved"]]),
                             width="stretch", hide_index=True)
            with st.expander("Latency breakdown (ms)"):
                st.json(res["latency_ms"])

with tab_review:
    items = api("GET", "/review") or []
    st.write(f"{len(items)} open item(s)")
    for it in items:
        with st.expander(f"#{it['id']} · {it['question']} · conf {it['confidence']:.2f} · {', '.join(it['reasons'])}"):
            st.write("**Model answer:**", it["response"]["answer"])
            st.json({"sources": [s["chunk_id"] for s in it["response"].get("sources", [])],
                     "route": it["response"].get("route")})
            text = st.text_area("Reviewer answer", key=f"res-{it['id']}")
            if st.button("Resolve", key=f"btn-{it['id']}", disabled=not text):
                api("POST", f"/review/{it['id']}/resolve", json={"resolution": text})
                st.rerun()

with tab_eval:
    files = sorted(REPORTS.glob("eval_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        st.info("No eval reports yet. Run `python -m policyrag.evaluation.evaluate --name baseline --gate`.")
    else:
        f = st.selectbox("Report", files, format_func=lambda p: p.stem)
        rep = json.loads(f.read_text(encoding="utf-8"))
        s = rep["summary"]
        c = st.columns(6)
        c[0].metric("Accuracy", s["answer_accuracy"])
        c[1].metric("Hit rate", s["retrieval"]["hit_rate"])
        c[2].metric("Faithfulness", s["faithfulness"])
        c[3].metric("Format valid", s["format"]["valid_rate"])
        c[4].metric("p95 latency", f"{s['latency_ms_p95']:.0f} ms")
        c[5].metric("Cost / 1k q", f"${s['cost_per_1k_queries_usd']}")
        if rep.get("gate"):
            g = rep["gate"]
            (st.success if g["passed"] else st.error)(f"Gate {'PASSED' if g['passed'] else 'FAILED'}")
            st.dataframe(pd.DataFrame(g["checks"]), hide_index=True, width="stretch")
        st.dataframe(pd.DataFrame(s["by_type"]).T, width="stretch")
        bad = [r for r in rep["rows"] if not r["correct"]]
        st.subheader(f"Incorrect cases ({len(bad)})")
        st.dataframe(pd.DataFrame([{k: r[k] for k in ("id", "type", "question", "expected", "answer", "status")}
                                   for r in bad]), hide_index=True, width="stretch")

with tab_mon:
    m = api("GET", "/metrics/summary")
    if m:
        c = st.columns(4)
        c[0].metric("Queries (window)", m["window_queries"])
        c[1].metric("p50 latency", f"{m['latency_ms_p50']} ms")
        c[2].metric("p95 latency", f"{m['latency_ms_p95']} ms")
        c[3].metric("Mean est. cost", f"${m['cost_usd_per_query_mean']:.6f}")
        st.json({"cache": m["cache"], "review_queue": m["review_queue"]})
        st.caption("Prometheus scrape endpoint: /metrics")
