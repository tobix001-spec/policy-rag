# Eval report: probe-amend-no-entity-filter

- run at: 2026-11-16T18:07:57+00:00
- cases: 15  |  judge: False  |  overrides: `{'entity_filter': False}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 15 |
| answer_accuracy | 0.8 |
| accuracy_answerable | 0.8 |
| abstention_accuracy | None |
| false_abstention_rate | 0.0 |
| hallucination_rate | None |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 0.8 |
| retrieval.hit_rate | 1.0 |
| retrieval.context_recall | 1.0 |
| retrieval.mrr | 0.7556 |
| retrieval.context_precision | 0.7556 |
| faithfulness | None |
| answer_relevancy | None |
| format.valid_rate | 1.0 |
| format.valid_first_try_rate | 1.0 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 1.0 |
| citations.relevant_rate | 0.9333 |
| review.flagged_rate | 0.0 |
| review.auto_answer_accuracy | 0.8 |
| review.error_recall | 0.0 |
| routing.complex.share | 0.9333 |
| routing.complex.accuracy | 0.7857 |
| routing.complex.latency_ms_p50 | 3477.4 |
| routing.complex.cost_usd_mean | 0.0003 |
| routing.simple.share | 0.0667 |
| routing.simple.accuracy | 1.0 |
| routing.simple.latency_ms_p50 | 3064.0 |
| routing.simple.cost_usd_mean | 0.0002 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 3476.4 |
| latency_ms_p95 | 3626.1 |
| llm_ms_p50 | 3369.9 |
| retrieval_ms_p50 | 82.0 |
| tokens_in_mean | 1189.7 |
| tokens_out_mean | 128.8 |
| cost_per_query_usd | 0.00024968 |
| cost_per_1k_queries_usd | 0.2497 |
| internal_leaks | 0 |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g107 | amendment | How much bodily injury coverage per person does Premier Auto provide? | Bodily injury liability limit for Premier Auto: $750,000 (per the latest amendment). | The Premier Auto policy provides bodily injury liability coverage of $500,000 per person. | answered |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | Multi-Pet reimburses 60% of eligible veterinary costs after the deductible is met. | answered |
| g114 | amendment | What is the specialist copay on Silver PPO? | Specialist visit copay for Silver PPO: $50 (per the latest amendment). | The specialist copay on Silver PPO is $75. | answered |
