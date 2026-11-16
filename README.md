# PolicyRAG

Production-style retrieval-augmented generation over insurance **policy, claims and support** documents,
running **fully locally** (Ollama + bge embeddings/reranker + FAISS) with an evaluation harness that
gates every change, structured JSON outputs, cost/latency accounting and a human-review queue.

> The corpus is synthetic: 189 documents for a fictional insurer, *Velmora Assurance*, generated from a
> fact registry. That is deliberate. Every golden-set question has a known answer **and** a known set
> of source documents, so retrieval and answer metrics are exact rather than judged.


## Results (measured, 180-case golden set, RTX 5070, qwen2.5 7b/3b)

Every version was built by reading the previous version's failures and fixing the cause. Each one was
then gated against its predecessor.

| metric | v0 | v1 | v2 | v3 | **v4 (current)** |
|---|---|---|---|---|---|
| answer accuracy | 78.3% | 86.1% | 93.3% | 94.4% | **93.9%** |
| accuracy of answers released without review | 77.0% | 89.2% | 94.9% | 97.1% | **96.3%** |
| wrong answers caught by the review gate | 12.8% | 44.0% | 41.7% | 60.0% | **54.5%** |
| faithfulness / answer relevancy (LLM judge) | 0.80 / 0.84 | 0.82 / 0.85 | 0.88 / 0.92 | 0.87 / 0.93 | **0.86 / 0.93** |
| retrieval hit rate / context recall | 99.4% / 97.4% | 100% / 99.0% | 100% / 99.7% | 100% / 99.7% | **100% / 99.7%** |
| hallucination rate (25 unanswerable) | 0% | 0% | 0% | 0% | **0%** |
| valid JSON | 100% | 100% | 100% | 99.4% | **100%** |
| internal-document leaks | 0 | 0 | 0 | 0 | **0** |
| latency p50 / p95 | 2.72 / 3.38 s | 2.74 / 3.48 s | 2.80 / 3.69 s | 2.76 / 3.68 s | **2.69 / 3.69 s** |
| est. cost per 1k queries | $0.158 | $0.170 | $0.182 | $0.364 ❌ | **$0.185** |
| gate | – | ✅ vs v0 | ✅ vs v1 | ❌ cost | ✅ vs v2 |

| question type (n) | v0 | v1 | v2 | v3 | **v4** |
|---|---|---|---|---|---|
| simple (105) | 85.7% | 85.7% | 95.2% | 94.3% | **94.3%** |
| amendment (15) | 33.3% | 100% | 86.7% | 100% | **100%** |
| comparison (25) | 44.0% | 60.0% | 84.0% | 88.0% | **88.0%** |
| internal, staff scope (10) | 100% | 100% | 90% | 90% | **80%** |
| unanswerable (25) | 100% | 100% | 100% | 100% | **100%** |

What changed and why:

| version | change | evidence that motivated it |
|---|---|---|
| v1 | query decomposition (one search per product named) | comparisons retrieved only one product (context recall 0.5) |
| v1 | deterministic grounding verifier (numbers + products must be in cited chunks) | wrong answers claimed ~0.93 self-confidence, so the review queue missed them |
| v1 | post-retrieval routing to 7b when an amendment is in play | the 3b model ignored amendments (33%) |
| v2 | **entity filter**: for one-product questions, sibling products' chunks rank last | ~11 errors were the 3b model copying a *sibling* product's number from identically templated sentences |
| v2 | `reasoning` is the first JSON field; values before the conclusion | the 7b model stated both values correctly, then named the wrong winner |
| v2 | 4 chunks per product in decomposed retrieval (was 3) | comparisons missed the exact section needed |
| v3 | **removed** "amendments first" context ordering (added in v2) | a 15-case probe: 86.7% with it, 100% without |
| v4 | 512-token output cap + escalate invalid 3b output to 7b | **v3's gate caught a runaway generation**: one answer looped for 16 min and doubled the run's cost |

**Grader corrections.** Two grader bugs were found and fixed during this work. All reports were
re-scored from their stored answers with the final grader ([`evaluation/rescore.py`](src/policyrag/evaluation/rescore.py)),
so every number above uses the same rule.
1. Comparison answers were marked correct whenever both values appeared, even when the answer named the
   **wrong winner**. This inflated v0/v1 (originally reported as 80.6% / 88.9%).
2. The first fix read the winner from the first product named in a sentence, which broke on
   "…$7,500 for A and $25,000 for B, **so B has the higher** limit". It now reads the concluding clause.

**Run-to-run noise.** Even at temperature 0, two runs of the same configuration differ by about 1–2
cases out of 180 (GPU nondeterminism in Ollama). v3 and v4 differ by one net case, which is within that
noise.

Full reports with every incorrect case: [`reports/`](reports/) (`eval_v0-baseline.md` … `eval_v4.md`).

### Ablations

These were run on the **v1** configuration, on a 90-case stratified subset, without the judge. Each
variant is compared with the reference run on the *same* 90 cases. The gate verdicts in
[`reports/ablations.md`](reports/ablations.md) compare a subset with the full-set baseline, so they
aren't like-for-like: read the deltas.

| variant | accuracy | Δ vs ref | amendment | comparison | errors caught by review | p50 | cost / 1k |
|---|---|---|---|---|---|---|---|
| **reference (v1)** | 84.3% | – | 100% | 33% | 43% | 2.68 s | $0.173 |
| no reranker | 76.4% | **−7.9** | 50% | 17% | 33% | 2.62 s | $0.160 |
| dense only (no BM25) | 83.2% | −1.1 | 100% | 33% | 47% | 2.72 s | $0.175 |
| k = 2 chunks | 86.5% | +2.2 | 88% | 33% | **25%** | 2.60 s | $0.128 |
| no query decomposition | 83.2% | −1.1 | 100% | 25% | 60% | 2.73 s | $0.170 |
| no amendment expansion | 84.3% | 0.0 | 100% | 33% | 57% | 2.76 s | $0.163 |
| no grounding verifier | 83.2% | −1.1 | 100% | 33% | **13%** | 2.72 s | $0.173 |
| everything → 3b | 78.6% | **−5.7** | **38%** | 42% | 32% | 2.65 s | $0.151 |
| everything → 7b | 86.5% | +2.2 | 100% | 33% | 25% | 3.03 s | **$0.220** |

* **The cross-encoder reranker carries the most weight** (−7.9 points; amendment accuracy halves).
* **The grounding verifier is a safety feature, not an accuracy feature.** Accuracy barely moves, but the
  share of wrong answers caught by review falls from 43% to 13%.
* **Routing is a real trade-off.** Everything on 7b gains 2.2 points for +27% cost and +13% latency.
  Everything on 3b loses 5.7 points, and amendment accuracy collapses to 38%.
* **BM25 and amendment expansion showed no measurable benefit** on this corpus. They are kept as cheap
  safety nets; the claim is "costs nothing", not "helps".
* **k = 2 is more accurate but less self-aware**: review catches far fewer errors.
* Caveat: subset comparison groups are small (12 comparison cases, 8 amendment cases), so ±1 case
  moves those columns 8–12 points.

### Known weak spots

* **Comparisons (88%)**. The remaining failures: an answer that uses a pre-amendment value; one that
  claims a value is "not specified" when it was retrieved; and one that contradicts itself ("Term 30
  has the faster … so Term 30 has the slower …").
* **Simple lookups (6 errors)**. Mostly appeal deadlines where the 3b model takes the *claim filing*
  deadline from the same product's guide.
* **Internal questions (80%)**. The 3b model abstains on both "SIU referral" questions (2 of 10, a small
  sample but a consistent pattern).
* **Data issues found by the eval, documented rather than silently fixed:** one generated amendment sets
  a pet reimbursement rate to an impossible **120%**, because amended values weren't capped. One amendment
  applies only to policies "issued or renewed on or after" its date, which makes the question
  "what is the limit?" arguably ambiguous. And one grader limitation: a bare "5" for "how many failed
  login attempts?" is graded wrong. Changing these after seeing results would move the goalposts.

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
   │    → one product named: entity filter (sibling products' chunks rank last)
   │    → 2+ products named: decomposition (one sub-retrieval per product, 4 chunks each)
   │    → amendment expansion (pull in docs that supersede a retrieved doc)
   ▼  generation/router.py — rules: comparison/reasoning/multi-part → qwen2.5:7b, else qwen2.5:3b
   │                         + post-retrieval upgrade when a relevant amendment is in context
   ▼  generation/generator.py — LCEL: prompt | llm.with_retry().with_fallbacks([other model])
   │    Ollama JSON-schema constrained decoding (reasoning field first, 512-token cap)
   │    → Pydantic validation → logged coercions → 1 LLM repair → invalid 3b output escalates to 7b
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
