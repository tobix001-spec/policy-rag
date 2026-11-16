# PolicyRAG

Production-style retrieval-augmented generation over insurance **policy, claims and support** documents,
running **fully locally** (Ollama + bge embeddings/reranker + FAISS) with an evaluation harness that
gates every change, structured JSON outputs, cost/latency accounting and a human-review queue.

> The corpus is synthetic: 189 documents for a fictional insurer, *Velmora Assurance*, generated from a
> fact registry. That is deliberate. Every golden-set question has a known answer **and** a known set
> of source documents, so retrieval and answer metrics are exact rather than judged.

## Results (measured, 180-case golden set, RTX 5070, qwen2.5 7b/3b)

The first full evaluation (**v0**) exposed three weaknesses: the small model mixed up neighbouring
facts and ignored amendments; single-query retrieval found only one side of two-product comparisons;
and wrong answers carried ~0.93 self-reported confidence, so the review queue missed them. **v1** adds
query decomposition, a deterministic grounding verifier and post-retrieval routing. It was gated
against v0 and promoted.

| metric | v0 | **v1** |
|---|---|---|
| answer accuracy | 80.6% | **88.9%** |
| accuracy of answers released without review | 79.7% | **93.1%** |
| wrong answers caught by the review gate | 14.3% | **55.0%** |
| retrieval hit rate / context recall | 99.4% / 97.4% | **100% / 99.0%** |
| faithfulness / answer relevancy (LLM judge) | 0.80 / 0.84 | 0.82 / 0.85 |
| hallucination rate on 25 unanswerable questions | 0% | 0% |
| valid JSON (schema-validated) | 100% | 100% |
| internal-document leaks to customers | 0 | 0 |
| latency p50 / p95 | 2.72 s / 3.38 s | 2.74 s / 3.48 s |
| est. API-equivalent cost per 1k queries | $0.158 | $0.170 |

Accuracy by question type:

| type | n | v0 | v1 |
|---|---|---|---|
| simple | 105 | 85.7% | 85.7% |
| amendment | 15 | 33.3% | **100%** |
| comparison | 25 | 60.0% | **80.0%** |
| internal (staff scope) | 10 | 100% | 100% |
| unanswerable | 25 | 100% | 100% |

Full reports: [`reports/eval_v0-baseline.md`](reports/eval_v0-baseline.md) and
[`reports/eval_v1.md`](reports/eval_v1.md), including every incorrect case.

### Ablations

Each variant runs on a 90-case stratified subset, without the judge, gated against v1. Full table:
[`reports/ablations.md`](reports/ablations.md).

| variant | accuracy | amendment acc. | comparison acc. | p50 latency | cost / 1k | gate |
|---|---|---|---|---|---|---|
| **full (v1)** | 87.6% | 100% | 58.3% | 2.68 s | $0.173 | ✅ |
| no reranker | 79.8% | 50.0% | 41.7% | 2.62 s | $0.160 | ❌ 10 checks |
| dense only (no BM25) | 86.5% | 100% | 58.3% | 2.72 s | $0.175 | ✅ |
| k = 2 chunks | 89.9% | 87.5% | 58.3% | 2.60 s | $0.128 | ❌ review recall |
| no query decomposition | 85.4% | 100% | 41.7% | 2.73 s | $0.170 | ❌ accuracy, recall |
| no amendment expansion | 87.6% | 100% | 58.3% | 2.76 s | $0.163 | ✅ |
| no grounding verifier | 86.5% | 100% | 58.3% | 2.72 s | $0.173 | ❌ review metrics |
| everything → 3b model | 82.0% | 37.5% | 66.7% | 2.65 s | $0.151 | ❌ 6 checks |
| everything → 7b model | 89.9% | 100% | 58.3% | 3.03 s | $0.220 | ❌ cost, review recall |

What the ablations show:

* **The cross-encoder reranker carries the most weight.** Without it, accuracy falls 7.8 points and
  amendment accuracy halves.
* **Query decomposition is what fixes comparisons.** Without it, comparison accuracy drops from 58% to
  42% and context recall falls.
* **The grounding verifier is a safety feature, not an accuracy feature.** Accuracy barely moves, but
  the share of wrong answers caught by review collapses from 55% to 17%.
* **Routing is a real trade-off.** Sending everything to the 7b model gains 2.3 points for +27% cost
  and +13% latency. Sending everything to the 3b model loses 5.6 points, and amendment accuracy falls
  to 37.5%. That is why amendment queries are upgraded after retrieval.
* **BM25 and amendment expansion showed no measurable benefit here.** Retrieval already surfaces the
  amendments directly. Both are kept as cheap safety nets, and the claim is that they cost nothing,
  not that they help.
* **k = 2 looks better on accuracy but fails the gate**, because review catches fewer errors.
  Caveat: on a 90-case subset, review recall rests on about 11 wrong answers, so a 2–3 case swing moves
  it 20 points. Treat that particular check as noisy at this sample size.

### Known weak spots

* **Comparisons are the weakest category** (80% on the full set). The remaining failures mostly
  involve products with amendments (old and new values both in context) or the model claiming a value
  is "not specified" when it was retrieved.
* **15 simple-lookup errors remain.** These are mostly the small model picking a neighbouring number
  from a chunk that states several facts.

> 📘 New to the project? Read [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md): every component
> explained, the metrics, the AWS production plan, known limitations, and interview Q&A.

## Architecture

```
data/raw/*.md (front matter: doc_type, line, product, last_updated, confidentiality, supersedes)
   │
   ▼  ingestion/chunking.py — heading-aware semantic chunking (+ recursive fallback, small-section merge)
   ▼  ingestion/embed_and_index.py — bge-small-en-v1.5 → FAISS IndexFlatIP (unit vectors = cosine)
   │
query ─► semantic cache (cosine ≥ 0.97 + entity guard + scope key) ──hit──► response
   │ miss
   ▼  retrieval/retriever.py
   │    access filter (confidentiality) → dense top-20 + BM25 top-20 → RRF
   │    → bge-reranker-base cross-encoder → top-5
   │    → multi-entity decomposition (one sub-retrieval per product named)
   │    → amendment expansion (pull in docs that supersede a retrieved doc)
   ▼  generation/router.py — rules: comparison/reasoning/multi-part → qwen2.5:7b, else qwen2.5:3b
   │                         + post-retrieval upgrade when a relevant amendment is in context
   ▼  generation/generator.py — LCEL: prompt | llm.with_retry().with_fallbacks([other model])
   │    Ollama JSON-schema constrained decoding → Pydantic validation → logged coercions → 1 LLM repair
   │    citation check (must be retrieved chunk ids) → grounding verifier (numbers + products)
   │    confidence = 0.5·rerank + 0.5·LLM, penalised by verifier findings
   ▼  low confidence / abstained / ungrounded ─► SQLite review queue (+ optional webhook)
   ▼  monitoring/metrics.py — Prometheus counters/histograms, JSONL query log, rolling p50/p95, est. cost
FastAPI (/query /evaluate /health /metrics /review)  ·  Streamlit UI  ·  docker compose
```

## Quick start (Windows, PowerShell)

```powershell
# keep the 5 GB CUDA venv out of OneDrive
$env:UV_PROJECT_ENVIRONMENT = "$env:USERPROFILE\.venvs\policy-rag"
uv sync --python 3.12 --extra ui --extra redis --group dev

ollama pull qwen2.5:7b; ollama pull qwen2.5:3b

uv run python -m policyrag.corpus.generate          # 189 docs, facts.json, golden_set.json (180 cases)
uv run python -m policyrag.ingestion.embed_and_index
uv run uvicorn policyrag.api.main:app --port 8000   # http://localhost:8000/docs
uv run streamlit run ui/app.py                      # http://localhost:8501
uv run pytest                                       # offline: fake models, ~2 s
```

```powershell
# evaluation + regression gate (exit code 1 on failure)
uv run python -m policyrag.evaluation.evaluate --name candidate --gate
uv run python -m policyrag.evaluation.evaluate --name v1 --update-baseline   # accept a new baseline
uv run python -m policyrag.evaluation.ablations --limit 90
```

Docker: `docker compose -f docker/docker-compose.yml up --build` (Ollama with GPU, Redis cache, API, UI).

## API

```http
POST /query            {"question": "...", "line": "health", "doc_types": ["policy"], "use_cache": true}
                       header X-Role: customer | staff   (staff may retrieve INTERNAL documents)
POST /evaluate         {"limit": 20, "judge": false, "gate": true}  → job id (runs in a subprocess)
GET  /evaluate/{id}    job status + tail of the gate output
GET  /health           index + Ollama + model availability
GET  /metrics          Prometheus exposition;  GET /metrics/summary  p50/p95, cost, cache, queue
GET  /review           open items;  POST /review/{id}/resolve  {"resolution": "..."}
```

Response contract (`PolicyAnswer.v1`): `answer`, `answerable`, `sources[]` (chunk id, title, section,
last_updated, snippet, rerank score), `confidence{final,retrieval,llm}`, `status` (`answered` |
`needs_review`), `review_reasons[]`, `route{name,model,fallback_used}`, `usage{tokens, cost_usd_estimate}`,
`latency_ms{total, retrieval.*, llm}`, `cache`, `format{valid_first_try, coerced, repaired}`.

## Evaluation

The golden set (`data/golden_set.json`, 180 cases) is generated alongside the corpus:

| type | n | what it tests |
|---|---|---|
| simple | 105 | single-fact lookup across 6 lines of business + company-wide support facts |
| amendment | 15 | value changed by a later amendment; the old value is still in the original policy |
| comparison | 25 | two sibling products, same attribute; answer must give both values |
| internal | 10 | confidential adjuster guidelines, staff scope |
| unanswerable | 25 | non-existent products (e.g. "Bronze PPO" next to a real "Bronze HMO"), absent attributes, internal docs requested with public scope, off-topic |

Metrics (all in `evaluation/evaluate.py`):

* **Deterministic (primary).** Answer accuracy is a boundary-aware fact match: `$1,500` ≠ `$15,000`
  and `20 days` ≠ `120 days`. Also measured: abstention accuracy, hallucination rate, retrieval hit
  rate, context recall, MRR, RAGAS-style context precision, citation validity/relevance, format
  validity (first try / after coercion / after repair), and internal-document leaks.
* **LLM-judged (secondary).** Faithfulness (atomic claims checked against the context) and answer
  relevancy (cosine between the question and questions regenerated from the answer). These follow the
  RAGAS definitions but are implemented directly against the local judge. Caveat: the judge is the same
  model family as the generator.
* **Production.** p50/p95 latency, tokens, estimated cost per 1k queries, routing mix and accuracy per
  route, **review error recall** (the share of wrong answers the review gate caught), and
  **auto-answer accuracy** (accuracy of answers released without review).

`config/eval_gate.yaml` holds absolute floors/ceilings (e.g. zero internal leaks, ≥ 98% valid JSON) and
max drops vs `reports/baseline.json`, which catch a regression that still clears the floor.

## Cost and latency

Local inference has no per-token bill. `cost_usd_estimate` prices the measured tokens at configurable
API-equivalent rates (`Settings.prices`: 7b ≈ gpt-4o-mini, 3b ≈ gpt-4.1-nano list prices), so routing and
caching savings can be expressed in dollars. Treat these figures as estimates, not invoices.

## Design notes

* **Why a synthetic corpus.** Real policy PDFs have no answer key, and LLM-written golden sets drift.
  Generating documents *from* facts makes every metric auditable; `tests/` asserts every registered fact
  literally appears in each document that claims it.
* **Semantic cache safety.** Sibling-product questions embed almost identically, so a hit also requires
  the same product/number/channel signature, the same access scope, and token overlap. Only `answered`
  results are cached.
* **Access control happens before the LLM.** Confidentiality is a retrieval filter, not a prompt
  instruction, and the eval counts leaks.
* **Confidence.** LLM self-reported confidence was uncalibrated in practice: wrong answers routinely
  claimed > 0.9. The deterministic grounding verifier (every number in the answer must occur in a cited
  chunk; every product in the question must occur in the cited chunks) is what drives review recall.

## Layout

```
src/policyrag/
  corpus/       catalog.py (products, attributes, phrasing variants) · generate.py
  ingestion/    load_docs.py · chunking.py · embed_and_index.py
  retrieval/    retriever.py (dense+BM25+RRF, filters, decomposition, amendments) · reranker.py
  generation/   prompts.py · router.py · generator.py · cache.py · review_queue.py
  evaluation/   golden_set.py · evaluate.py (metrics + gate) · judge.py · ablations.py
  api/          main.py · schemas.py · middleware.py
  monitoring/   metrics.py
  config.py · providers.py (local + fake providers) · textnorm.py
config/eval_gate.yaml · docker/ · ui/app.py · tests/ · reports/
```
