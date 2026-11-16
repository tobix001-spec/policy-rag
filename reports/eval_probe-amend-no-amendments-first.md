# Eval report: probe-amend-no-amendments-first

- run at: 2026-11-16T18:06:41+00:00
- cases: 15  |  judge: False  |  overrides: `{'amendments_first': False}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 15 |
| answer_accuracy | 1.0 |
| accuracy_answerable | 1.0 |
| abstention_accuracy | None |
| false_abstention_rate | 0.0 |
| hallucination_rate | None |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 1.0 |
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
| citations.relevant_rate | 1.0 |
| review.flagged_rate | 0.0 |
| review.auto_answer_accuracy | 1.0 |
| review.error_recall | 1.0 |
| routing.complex.share | 0.9333 |
| routing.complex.accuracy | 1.0 |
| routing.complex.latency_ms_p50 | 3469.0 |
| routing.complex.cost_usd_mean | 0.0003 |
| routing.simple.share | 0.0667 |
| routing.simple.accuracy | 1.0 |
| routing.simple.latency_ms_p50 | 3116.7 |
| routing.simple.cost_usd_mean | 0.0002 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 3463.1 |
| latency_ms_p95 | 3606.2 |
| llm_ms_p50 | 3375.1 |
| retrieval_ms_p50 | 85.4 |
| tokens_in_mean | 1159.2 |
| tokens_out_mean | 128.9 |
| cost_per_query_usd | 0.00024533 |
| cost_per_1k_queries_usd | 0.2453 |
| internal_leaks | 0 |
