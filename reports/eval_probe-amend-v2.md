# Eval report: probe-amend-v2

- run at: 2026-11-16T18:05:25+00:00
- cases: 15  |  judge: False  |  overrides: `{}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 15 |
| answer_accuracy | 0.8667 |
| accuracy_answerable | 0.8667 |
| abstention_accuracy | None |
| false_abstention_rate | 0.0 |
| hallucination_rate | None |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 0.8667 |
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
| citations.relevant_rate | 0.8667 |
| review.flagged_rate | 0.0 |
| review.auto_answer_accuracy | 0.8667 |
| review.error_recall | 0.0 |
| routing.complex.share | 0.9333 |
| routing.complex.accuracy | 0.8571 |
| routing.complex.latency_ms_p50 | 3519.2 |
| routing.complex.cost_usd_mean | 0.0002 |
| routing.simple.share | 0.0667 |
| routing.simple.accuracy | 1.0 |
| routing.simple.latency_ms_p50 | 3082.5 |
| routing.simple.cost_usd_mean | 0.0002 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 3518.7 |
| latency_ms_p95 | 3661.7 |
| llm_ms_p50 | 3426.8 |
| retrieval_ms_p50 | 85.4 |
| tokens_in_mean | 1159.2 |
| tokens_out_mean | 124.2 |
| cost_per_query_usd | 0.0002425 |
| cost_per_1k_queries_usd | 0.2425 |
| internal_leaks | 0 |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g107 | amendment | How much bodily injury coverage per person does Premier Auto provide? | Bodily injury liability limit for Premier Auto: $750,000 (per the latest amendment). | The Premier Auto policy provides bodily injury liability coverage of $500,000 per person. | answered |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | The Multi-Pet plan reimburses 60% of eligible veterinary costs after the deductible. | answered |
