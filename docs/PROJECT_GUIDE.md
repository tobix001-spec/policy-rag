# PolicyRAG: The Complete Guide

What the project is, how every part works, how to run it, how to take it to production on AWS, and
what to say about it in an interview.

---

## 1. The one-paragraph version

PolicyRAG answers questions about insurance documents (policies, claims procedures, support articles).
A user asks *"How long do I have to appeal a denied Gold PPO claim?"*. The system finds the relevant
passages among ~190 documents, has an LLM answer **only from those passages**, returns the answer as
validated JSON with citations, checks that the answer is actually grounded in what it cited, and sends
anything doubtful to a human review queue. Every query is measured (latency, tokens, estimated cost),
and every change is tested against a 180-question golden set with a pass/fail **regression gate**.

---

## 2. What problem it solves

| Without it | With it |
|---|---|
| A staff member searches PDFs manually (the spec assumes ~15 min per lookup) | An answer with sources in ~3–6 s (measured on an RTX 5070) |
| Answers vary by who looks it up | Same pipeline, same rules, every time |
| An outdated document gets quoted | Amendments are pulled in automatically and override the old value |
| Customers could see internal rules | Confidential documents are filtered out *before* the LLM sees anything |
| No idea if quality is slipping | The eval gate fails the build when a metric drops |

---

## 3. Glossary (terms you must be able to explain)

- **RAG (retrieval-augmented generation).** Retrieve relevant text first, then let an LLM answer
  using only that text. This reduces hallucination and lets you cite sources.
- **Embedding.** A text turned into a vector (384 numbers here) so that similar meanings sit close
  together.
- **FAISS.** Facebook's vector-search library. `IndexFlatIP` is an exact inner-product search; on unit
  vectors it equals cosine similarity.
- **BM25.** Classic keyword search scoring. It is good at exact terms like "Gold PPO" or "SR-22",
  which embeddings sometimes blur.
- **Hybrid retrieval.** Dense (FAISS) plus sparse (BM25) results combined.
- **RRF (reciprocal rank fusion).** Merges two ranked lists: `score = Σ 1/(60 + rank)`. It needs no
  score normalisation.
- **Cross-encoder reranker.** A model that reads (question, passage) *together* and scores relevance.
  It is slower but much more accurate than embeddings, so it only runs on the top ~40 candidates.
- **Chunk.** A piece of a document (~300 characters here) that gets embedded and retrieved.
- **Semantic chunking.** Splits text where the meaning shifts, measured by embedding distance between
  neighbouring sentences.
- **Golden set.** Questions with known correct answers, used for testing.
- **Faithfulness.** The share of claims in the answer that the context supports.
- **Context recall.** Whether the retrieved chunks contained the facts needed.
- **p95 latency.** 95% of requests are faster than this number.
- **Regression gate.** A script that exits with code 1 (failing CI) when quality drops.
- **Human-in-the-loop.** Uncertain answers are routed to a person instead of the user.

---

## 4. Architecture: the path a question takes

```
User question  ──►  FastAPI /query  (X-Role header → access scope)
                       │
   1. Semantic cache ──┤ cosine ≥ 0.97 AND same products/numbers AND same scope → return cached answer
                       │ miss
   2. Retrieval        │ filter by confidentiality / doc_type / line
                       │ FAISS top-20  +  BM25 top-20  →  RRF merge
                       │ cross-encoder rerank → top-5
                       │ if ≥2 products named → one sub-search per product, interleaved
                       │ if a retrieved doc was amended → add the amendment chunk
   3. Routing          │ comparison / "why" / multi-part / long → qwen2.5:7b, else qwen2.5:3b
                       │ relevant amendment in context → upgrade to 7b
   4. Generation       │ LangChain LCEL: prompt | llm.with_retry().with_fallbacks([other model])
                       │ Ollama constrained JSON decoding
   5. Validation       │ Pydantic → logged coercions (e.g. 99 → 0.99) → 1 LLM repair attempt
   6. Verification     │ citations must be retrieved chunk ids
                       │ every number in the answer must appear in a cited chunk
                       │ every product in the question must appear in the cited chunks
   7. Confidence       │ 0.5 × rerank score + 0.5 × LLM confidence, × penalties
   8. Decision         │ abstained / low confidence / ungrounded → SQLite review queue
   9. Telemetry        │ Prometheus counters, JSONL log, tokens, estimated cost
                       ▼
                JSON response (answer, sources, confidence, status, route, usage, latency)
```

---

## 5. Every folder and file

```
policy-rag/
├── pyproject.toml            dependencies; torch from the CUDA 12.8 index on Windows
├── requirements.txt          pinned deps for Docker/CI (torch installed separately)
├── config/eval_gate.yaml     regression thresholds
├── data/
│   ├── raw/*.md              189 documents with YAML front matter
│   ├── facts.json            379 facts: value, accepted spellings, which docs state it
│   ├── golden_set.json       180 test cases
│   ├── index/                FAISS index + chunks.jsonl + manifest.json (generated)
│   └── review_queue.sqlite   human review items (generated)
├── src/policyrag/
│   ├── config.py             every setting; override with POLICYRAG_<NAME> env vars
│   ├── providers.py          local models (bge, Ollama) and fake ones for tests
│   ├── textnorm.py           "$1,500" == "1500 dollars"; boundary-safe matching
│   ├── corpus/catalog.py     the fictional insurer: 36 products, attributes, phrasings
│   ├── corpus/generate.py    builds docs + facts + golden set from the catalog
│   ├── ingestion/load_docs.py     reads .md (front matter), .txt, .pdf
│   ├── ingestion/chunking.py      heading-aware semantic chunker + recursive fallback
│   ├── ingestion/embed_and_index.py   embeds chunks, writes FAISS + manifest
│   ├── retrieval/retriever.py     filters, dense, BM25, RRF, decomposition, amendments
│   ├── retrieval/reranker.py      cross-encoder scores → sigmoid
│   ├── generation/prompts.py      system prompt + output schema (PolicyAnswer.v1)
│   ├── generation/router.py       rules for cheap vs strong model
│   ├── generation/generator.py    the full query pipeline (AnswerService)
│   ├── generation/cache.py        semantic cache (memory or Redis) with entity guard
│   ├── generation/review_queue.py SQLite queue + optional webhook (e.g. Slack)
│   ├── evaluation/golden_set.py   test case schema, stratified sampling
│   ├── evaluation/evaluate.py     metrics, gate, reports
│   ├── evaluation/judge.py        LLM-as-judge: faithfulness, answer relevancy
│   ├── evaluation/ablations.py    turn one component off at a time
│   ├── api/main.py                FastAPI endpoints
│   ├── api/schemas.py             request/response models
│   ├── api/middleware.py          request ids, access logs, error handler
│   └── monitoring/metrics.py      Prometheus metrics, query log, cost function
├── ui/app.py                 Streamlit demo (Ask / Review / Evaluation / Monitoring tabs)
├── tests/                    22 offline tests with fake models (~2 s)
├── docker/Dockerfile, docker-compose.yml
├── scripts/run_eval_pipeline.ps1   v0 → v1 → ablations
├── .github/workflows/ci.yml  tests on every push; eval gate on a GPU runner
└── reports/                  eval_*.json / eval_*.md, baseline.json, ablations.md
```

---

## 6. The data: why it is synthetic, and what is in it

**Fictional company:** *Velmora Assurance*, with 6 lines of business (health, auto, home, travel, pet,
life) and 6 products each, so 36 products.

| Document type | Count | Contents |
|---|---|---|
| Policy documents | 36 | Coverage, cost sharing, exclusions, terms, legal boilerplate |
| Claims guides | 36 | Filing deadline, decision time, appeals |
| Brochures | 36 | Marketing restatement of 2 facts (duplicate-source realism) |
| Amendments | 18 | Change one value; supersede the policy doc |
| Support articles | 51 | Company-wide facts (upload limits, password reset...) + noise articles |
| Internal memos | 12 | Confidential adjuster thresholds |
| **Total** | **189** | → **449 chunks** |

**Why synthetic.** Every document is generated *from* a fact registry, so for every test question we
know the exact answer and the exact documents containing it. That makes the metrics exact rather than
opinions. A test (`test_every_fact_is_stated_in_its_documents`) proves each fact literally appears
where the registry says.

**Deliberately hard parts:**
- Sibling products with near-identical wording but different values
- Old values still present in the original document after an amendment
- Web vs mobile articles with different limits for the same task
- Fake products that look real: "Bronze PPO" exists only as a "Bronze HMO"
- Confidential documents that must never reach customers

**Golden set (180):** 105 simple, 15 amendment, 25 comparison, 10 internal, 25 unanswerable.

---

## 7. How each component works (and why it was chosen)

### Chunking
1. Split by Markdown headings, so a chunk never mixes two sections.
2. Split sections into sentences; bullet lists stay whole.
3. Embed every sentence in one batch; break where the neighbour distance is above the document's 85th
   percentile.
4. Merge pieces under 200 characters; split pieces over 1,200 with the recursive splitter.
5. Merge tiny sections ("Who Is Affected") into the next one. This cut 733 chunks to 449.
6. Embed `"<doc title> | <section>\n<text>"`. The title header is what separates Gold PPO from
   Silver PPO.

### Retrieval
- The access filter runs first: customers see `public` only; staff see `public` + `internal`.
- Dense and BM25 run in parallel and are merged with RRF, then the cross-encoder reranks.
- **Decomposition:** "Senior Pet vs Pet Wellness" becomes two searches. The first eval showed a single
  search found only one product (context recall 0.5 on comparisons).
- **Amendment expansion:** if a retrieved chunk's document has an amendment, the amendment is added.
- **Entity filter (v2):** if the question names exactly one product, chunks of *other* products rank
  last. Every claims guide uses the same sentence template, so sibling chunks were distractors the 3b
  model copied numbers from.
- **Tried and removed (v3):** listing amendments first in the context. It measured worse (86.7% vs
  100% on amendment questions), so the context keeps plain rerank order.

### Routing (cost)
These are regex rules, not a classifier: they're transparent, cost nothing, and are easy to audit.
After retrieval, a strongly relevant amendment upgrades the query to the 7b model, because the 3b
model ignored amendments in the first eval.

### Generation and validation
- The prompt has rules plus one example of valid JSON.
- Ollama constrained decoding enforces the JSON *shape* but not numeric bounds, so the 3b model
  sometimes returns `"confidence": 99`. A logged coercion fixes it, and one LLM repair call handles
  the rest.
- Retry once, then fall back to the other model. If both fail, the user still gets a response,
  routed to review (never a 500).
- `reasoning` is the **first** JSON field, so the model writes its working before the answer. Ollama
  generates fields in schema order. This fixed comparisons where the right values led to the wrong
  winner.
- **512-token output cap + escalation (v4):** v3's gate caught a 3b answer that looped for 16 minutes.
  Output is now capped, and an invalid 3b output is retried once on the 7b model.

### Confidence and review
- LLM self-confidence turned out to be **uncalibrated**: wrong answers claimed about 0.93.
- So a deterministic **grounding verifier** checks the numbers and product names against the cited
  text.
- An item goes to review when the model abstains, the output is invalid, a citation is invalid or
  missing, the answer is ungrounded, or confidence is below 0.55.

### Semantic cache
"Deductible for Silver PPO" and "...for Gold PPO" can embed almost identically. A cache hit therefore
needs all of: high similarity, the same products/numbers/channel words, the same access scope, and
token overlap. Only clean `answered` results are cached.

---

## 8. Evaluation: the most important part for interviews

**Run it:**
```powershell
uv run python -m policyrag.evaluation.evaluate --name candidate --gate
```

| Metric | Meaning | Kind |
|---|---|---|
| answer_accuracy | Correct answers (answerable: required facts present; unanswerable: abstained) | exact |
| hallucination_rate | Unanswerable questions that got an answer anyway | exact |
| retrieval.hit_rate / context_recall / mrr / context_precision | Did search find the right chunks, and how high | exact |
| format.valid_rate | Responses that are valid JSON matching the schema | exact |
| citations.valid_rate | Cited chunks were actually retrieved | exact |
| review.auto_answer_accuracy | Accuracy of answers released *without* review | exact |
| review.error_recall | Share of wrong answers that the review gate caught | exact |
| faithfulness, answer_relevancy | Judged by qwen2.5:7b (RAGAS definitions) | LLM-judged |
| latency p50/p95, cost/1k queries | Speed and estimated spend | measured |
| internal_leaks | Confidential chunks shown to customers (must be 0) | exact |

**The gate** (`config/eval_gate.yaml`) has two kinds of check:
- **Floors:** absolute product requirements (≥ 98% valid JSON, 0 leaks...).
- **Max drop vs baseline:** catches a change that still clears the floor but got worse.

**Ablations** turn off one component at a time to prove what each one is worth, and whether the gate
catches its removal. Results land in `reports/ablations.md`.

> Numbers: the README's Results section has the full v0 → v4 history (78.3% → 93.9% accuracy) and the
> ablation deltas. Per-case detail is in `reports/eval_*.md`. Quote only measured numbers.

**Lessons from the eval loop (good interview material):**
1. **Grade the grader.** The comparison grader accepted answers that named the wrong winner. It was
   found by reading cases by hand, fixed, tested, and every report was re-scored.
2. **Intuition loses to measurement.** "Show the model the newest information first" sounded right and
   made amendment answers worse.
3. **The gate catches things accuracy can't.** A runaway generation barely moved accuracy or p95 but
   doubled cost, and only the cost check failed.
4. **Know your noise floor.** Identical configs differ by 1–2 cases per run, so ±1 point is not a
   result.

---

## 9. Running it locally

```powershell
cd policy-rag
$env:UV_PROJECT_ENVIRONMENT = "$env:USERPROFILE\.venvs\policy-rag"   # venv outside OneDrive

uv run python -m policyrag.corpus.generate            # docs + golden set
uv run python -m policyrag.ingestion.embed_and_index  # FAISS index
uv run uvicorn policyrag.api.main:app --port 8000     # API → http://localhost:8000/docs
uv run streamlit run ui/app.py                        # UI  → http://localhost:8501
uv run pytest                                         # offline tests
```

Example request:
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/query -ContentType application/json `
  -Headers @{ "X-Role" = "customer" } `
  -Body '{"question": "What is the annual deductible for the Gold PPO plan?"}'
```

Useful settings (environment variables):

| Variable | Default | Effect |
|---|---|---|
| POLICYRAG_LLM_DEFAULT / POLICYRAG_LLM_SMALL | qwen2.5:7b / qwen2.5:3b | Models |
| POLICYRAG_CONFIDENCE_THRESHOLD | 0.55 | Below this → review |
| POLICYRAG_FINAL_K | 5 | Chunks given to the LLM |
| POLICYRAG_HYBRID / POLICYRAG_RERANK | true | Turn BM25 / reranker on or off |
| POLICYRAG_CACHE_BACKEND | memory | `redis` for shared cache |
| POLICYRAG_PROVIDER | local | `fake` = no models (tests) |
| POLICYRAG_REVIEW_WEBHOOK | – | Slack-style webhook for review alerts |

**Using your own documents:** put `.md`/`.txt`/`.pdf` files in `data/raw/` (front matter optional),
rebuild the index, and write a golden set by hand. The generator only knows the synthetic corpus.

---

## 10. Taking it to production on AWS

### 10.1 What must change in the code first (honest list)

The current code is production-*style*. Before real users, change these:

| Current | Production replacement | Why |
|---|---|---|
| `X-Role` header trusted from the client | JWT from Amazon Cognito (or your SSO); role taken from the token claims | Anyone can send `X-Role: staff` today |
| SQLite review queue | Amazon RDS for PostgreSQL (or Aurora Serverless v2) | SQLite is one file on one machine; containers are ephemeral |
| FAISS file built at image build | Index built by an ingestion job, stored in S3, loaded at startup; at larger scale, OpenSearch Serverless (vector) or pgvector | New documents shouldn't need a new image |
| Ollama | vLLM (or TGI) on GPU, or Amazon Bedrock | Ollama is built for one user at a time; vLLM batches many concurrent requests |
| JSONL log files | stdout JSON → CloudWatch Logs | Containers lose local files |
| Redis cache scans every key | Redis with vector search (Redis Stack / MemoryDB), or keep only the exact-match cache | A scan is O(n) per lookup |
| `/evaluate` launches a subprocess in the API | A separate batch job (ECS task or CodeBuild) | Eval shouldn't compete with live traffic |
| Synthetic corpus | Real documents + parsing (Amazon Textract for scanned PDFs) + a hand-written golden set | The real goal |
| No rate limiting | AWS WAF rate rules + API Gateway usage plans | Abuse and cost protection |
| No PII handling | Redact PII before logging (Amazon Comprehend PII detection or a regex layer) | Claims data contains personal data |

### 10.2 Target architecture

```
                 Users (browser / internal tools)
                            │ HTTPS
                  Route 53 → CloudFront + AWS WAF
                            │
                Application Load Balancer (TLS via ACM)
              ┌─────────────┴──────────────┐
        ECS Fargate: UI            ECS Fargate: API (FastAPI, 2+ tasks, autoscaling)
        (Streamlit or a           │  embeddings + reranker on CPU (or a small GPU task)
         React app on S3)         │  FAISS index loaded from S3 at startup
                                  │
          ┌──────────────┬────────┼───────────────┬──────────────────┐
          ▼              ▼        ▼               ▼                  ▼
   ElastiCache      RDS Postgres  LLM service     Cognito          Secrets Manager
   (Redis cache)    (review queue, ECS on EC2 GPU  (users, roles)   (DB creds, keys)
                    audit log)    g5/g6 + vLLM
                                  ── or ── Amazon Bedrock

 Ingestion:  S3 bucket (raw docs) ─event─► EventBridge ─► Step Functions:
             parse (Textract) → chunk → embed → build index → run eval gate → publish index to S3
             → roll API tasks (only if the gate passes)

 Observability: CloudWatch Logs + metrics/alarms, Amazon Managed Prometheus + Grafana (scrapes /metrics),
                X-Ray / OpenTelemetry traces
 CI/CD:         GitHub Actions → tests → build image → push to ECR → eval gate → deploy ECS (blue/green)
```

### 10.3 Choosing where the LLM runs

| Option | Pros | Cons | Best when |
|---|---|---|---|
| **Self-hosted on EC2 GPU** (g5.xlarge A10G 24 GB, or g6.xlarge L4 24 GB) with vLLM serving Qwen2.5-7B | Data stays in your VPC; fixed cost; same models as now | You run patching, scaling, GPUs | High, steady volume; strict data rules |
| **Amazon Bedrock** (Claude, Llama, Mistral, Titan embeddings) | No GPUs to manage; pay per token; scales | Per-token cost; code changes to the provider layer | Variable traffic; fastest to production |
| **OpenAI API** (the stack in the original spec) | Matches the resume stack (gpt-4o-mini, text-embedding-3-small) | Data leaves AWS; needs a vendor agreement | Prototyping; non-sensitive data |

Switching is contained: `providers.py` is the only file that builds models. Add a provider (e.g.
`ChatBedrockConverse` from `langchain-aws`) and set `POLICYRAG_PROVIDER`. If you change the embedding
model you **must rebuild the index**; the retriever refuses a mismatched index on purpose.

### 10.4 Step-by-step deployment (self-hosted path)

1. **Account setup.** Separate dev/prod accounts (AWS Organizations), IAM Identity Center for people,
   and least-privilege IAM roles for each service. Turn on CloudTrail.
2. **Network.** A VPC across 2 Availability Zones, with public subnets (ALB only) and private subnets
   (everything else). Use VPC endpoints for S3, ECR and Secrets Manager so traffic stays private.
3. **Container registry.** Create ECR repositories `policyrag-api` and `policyrag-llm`; build and push
   from GitHub Actions using OIDC (no long-lived keys).
4. **Storage.** Create S3 buckets `policyrag-raw-docs` (versioning on, SSE-KMS) and
   `policyrag-index` (versioned index artifacts: `index.faiss`, `chunks.jsonl`, `manifest.json`).
5. **Database.** RDS PostgreSQL (Multi-AZ in prod) for the review queue and audit log. Port
   `review_queue.py` from `sqlite3` to `psycopg`/SQLAlchemy; the schema is the same.
6. **Cache.** ElastiCache for Redis in private subnets. Set `POLICYRAG_CACHE_BACKEND=redis` and
   `POLICYRAG_REDIS_URL` from Secrets Manager.
7. **LLM service.** An ECS cluster with an EC2 GPU capacity provider (ECS GPU-optimized AMI). Run vLLM
   serving the model behind an internal load balancer. vLLM speaks the OpenAI API, so add an
   OpenAI-compatible provider pointing at it.
8. **API service.** ECS Fargate (or EC2 if you want GPU for the reranker), 2+ tasks behind the ALB.
   Health check `/health`; autoscale on CPU and request count. At startup the task downloads the
   index version named in `POLICYRAG_INDEX_VERSION` from S3.
9. **Auth.** A Cognito user pool with groups `customer` and `staff`; have the ALB authenticate or
   validate the JWT in FastAPI, and map the group to `allowed_confidentiality`. Delete the
   `X-Role` header path.
10. **Edge.** CloudFront + WAF (managed rule sets + rate limit) + an ACM certificate + a Route 53
    domain.
11. **Ingestion pipeline.** An S3 upload triggers EventBridge, which triggers Step Functions: parse
    (Textract for scanned PDFs), then chunk + embed + index (an ECS task running `embed_and_index`),
    then the eval gate (an ECS task running `evaluate --gate`). Only on pass: write the new index
    version to S3 and update the ECS service, a rolling or blue/green deploy.
12. **Observability.** Containers log JSON to stdout, which lands in CloudWatch Logs. Amazon Managed
    Prometheus scrapes `/metrics`, and Grafana shows the dashboards. Set alarms on p95 latency, error
    rate, review-queue growth, fallback rate, and GPU utilisation.
13. **CI/CD.** On a PR: unit tests. On merge: build, push to ECR, run the eval gate on a GPU runner,
    deploy to staging, smoke test, then a manual approval for prod.
14. **Backups and DR.** RDS automated backups + snapshots, S3 versioning, and the index is
    reproducible from raw docs. Write down the restore steps and test them.

### 10.5 Rough monthly cost (us-east-1, on-demand, always on; check current pricing)

| Item | Approx. |
|---|---|
| 1 × g6.xlarge (L4) or g5.xlarge (A10G) GPU for the LLM | ~$600–750 |
| 2 × Fargate tasks (2 vCPU / 8 GB) for the API | ~$140 |
| ALB + data transfer | ~$25–50 |
| RDS PostgreSQL db.t4g.small (Multi-AZ doubles it) | ~$30–60 |
| ElastiCache cache.t4g.small | ~$25 |
| S3, CloudWatch, Secrets Manager, WAF | ~$30–60 |
| **Total** | **~$850–1,100 / month** |

Ways to cut it: stop the GPU outside business hours (scheduled scaling), use Savings Plans/Spot for
non-critical environments, or use Bedrock per-token pricing if traffic is low. This project's
`cost_per_1k_queries_usd` metric tells you which option is cheaper at your volume.

### 10.6 Security checklist
- [ ] Access scope comes from the authenticated identity, never from a client header
- [ ] Encryption at rest (KMS on S3, RDS, ElastiCache) and in transit (TLS everywhere)
- [ ] Private subnets for everything except the ALB; security groups allow only the needed ports
- [ ] Secrets in Secrets Manager, never in images or env files in git
- [ ] PII redacted before logs; log retention policy set
- [ ] **Prompt injection:** documents could contain "ignore previous instructions". Keep the LLM
      tool-less (it is), validate the output schema (it does), and review uploads to the raw bucket
- [ ] Audit log of who asked what and which documents were returned (compliance)
- [ ] Image scanning in ECR; dependency updates on a schedule

### 10.7 Operating it
- **Weekly:** review the queue. Resolved items become new golden cases, which improves the eval over
  time.
- **On every document update:** the ingestion pipeline reruns the eval gate before publishing.
- **On every code change:** CI runs the gate against the accepted baseline.
- **Watch for:** rising review rate (documents drifting from questions), rising fallback rate (LLM
  instability), and p95 creeping up (load or longer contexts).

---

## 11. Known limitations (say these before an interviewer finds them)

1. **Synthetic data.** The metrics prove the pipeline works on realistic generated documents, not
   on a real insurer's PDFs.
2. **The judge shares a model family with the generator.** Faithfulness and relevancy may be biased
   upward; the exact metrics are the primary signal.
3. **Rule-based routing** can misroute unusual phrasings. The eval reports accuracy per route to
   catch this.
4. **The grounding verifier checks numbers and product names**, not every kind of claim (e.g. a
   wrong condition with no number in it).
5. **The cache's entity guard** relies on known product names; new products need the index rebuilt.
6. **Single-process state:** SQLite and the in-memory cache must move to Postgres/Redis for multiple
   replicas (section 10.1).
7. **The 15-minute manual baseline is an assumption** from the spec, not something measured here.

---

## 12. Interview questions you should be ready for

- **Why hybrid retrieval?** Embeddings blur exact names ("Gold PPO" vs "Silver PPO"); BM25 nails
  exact terms. RRF merges them without score calibration. The ablation shows the measured
  difference.
- **Why rerank?** The bi-encoder is fast but shallow. The cross-encoder reads the query and passage
  together. It's too slow for the whole corpus, so it reranks only the ~40 candidates.
- **How do you prevent hallucination?** Answer-only-from-context rules, abstention on missing info,
  citation checks, the grounding verifier, review routing, and a measured hallucination rate on 25
  unanswerable questions.
- **How do you know a change didn't break anything?** The golden set + gate: absolute floors plus
  max-drop vs baseline, with a non-zero exit code in CI.
- **How is the eval trustworthy?** Documents are generated from facts, so answers are known; a test
  proves each fact appears in its documents; matching is boundary-aware.
- **Why not trust the LLM's confidence?** It was measured: wrong answers carried ~0.93. Deterministic
  verification replaced it as the review trigger.
- **How does it handle outdated documents?** Amendment expansion pulls in the superseding document;
  the prompt says amendments win; and post-retrieval routing sends those queries to the stronger
  model.
- **How would you scale it?** Section 10: vLLM for concurrent LLM serving, stateless API replicas,
  Postgres + Redis for state, the index in S3 or OpenSearch, and an ingestion pipeline with an eval
  gate.
- **What would you do next?** Real documents and a hand-labelled golden set, an independent judge
  model, a learned router, query rewriting for vague questions, and streaming responses.
