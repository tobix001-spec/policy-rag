# Eval report: v3

- run at: 2026-11-16T18:45:24+00:00
- cases: 180  |  judge: True  |  overrides: `{}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 180 |
| answer_accuracy | 0.9444 |
| accuracy_answerable | 0.9355 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.0194 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 1.0 |
| by_type.comparison.n | 25 |
| by_type.comparison.accuracy | 0.88 |
| by_type.internal.n | 10 |
| by_type.internal.accuracy | 0.9 |
| by_type.simple.n | 105 |
| by_type.simple.accuracy | 0.9429 |
| by_type.unanswerable.n | 25 |
| by_type.unanswerable.accuracy | 1.0 |
| retrieval.hit_rate | 1.0 |
| retrieval.context_recall | 0.9968 |
| retrieval.mrr | 0.9516 |
| retrieval.context_precision | 0.9478 |
| faithfulness | 0.87 |
| answer_relevancy | 0.9251 |
| format.valid_rate | 0.9944 |
| format.valid_first_try_rate | 0.9944 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 1.0 |
| citations.relevant_rate | 0.9211 |
| review.flagged_rate | 0.2444 |
| review.auto_answer_accuracy | 0.9706 |
| review.error_recall | 0.6 |
| routing.complex.share | 0.2333 |
| routing.complex.accuracy | 0.9286 |
| routing.complex.latency_ms_p50 | 3479.4 |
| routing.complex.cost_usd_mean | 0.0003 |
| routing.simple.share | 0.7667 |
| routing.simple.accuracy | 0.9493 |
| routing.simple.latency_ms_p50 | 2730.0 |
| routing.simple.cost_usd_mean | 0.0004 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2764.8 |
| latency_ms_p95 | 3683.7 |
| llm_ms_p50 | 2667.9 |
| retrieval_ms_p50 | 89.5 |
| tokens_in_mean | 1203.7 |
| tokens_out_mean | 553.3 |
| cost_per_query_usd | 0.00036393 |
| cost_per_1k_queries_usd | 0.3639 |
| internal_leaks | 0 |

## Gate: FAIL

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.9444 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.9355 | 0.8 | ✅ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9968 | 0.85 | ✅ |
| format.valid_rate | >= floor | 0.9944 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 1.0 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.9706 | 0.9 | ✅ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3683.7 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.9444 | 0.9033 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.9355 | 0.8926 | ✅ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9968 | 0.9668 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9516 | 0.9016 | ✅ |
| faithfulness | drop <= 0.05 vs baseline | 0.87 | 0.8338 | ✅ |
| answer_relevancy | drop <= 0.05 vs baseline | 0.9251 | 0.8742 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 0.9944 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.9706 | 0.9189 | ✅ |
| review.error_recall | drop <= 0.1 vs baseline | 0.6 | 0.3167 | ✅ |
| latency_ms_p95 | <= 1.3x baseline | 3683.7 | 4795.83 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00036393 | 0.0002 | ❌ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g001 | simple | What is the grace period for late premiums on Final Expense? | Premium grace period for Final Expense: 45 days. | The grace period for late premiums on Final Expense is 15 days. | needs_review |
| g013 | simple | What is the appeal deadline for Renters Essential? | Appeal deadline for Renters Essential: 90 days. | The appeal deadline for Renters Essential is 120 days from the loss. | needs_review |
| g019 | simple | How long do I have to appeal a denied HomeBasic claim? | Appeal deadline for HomeBasic: 30 days. | You have 75 days to appeal a denied HomeBasic claim. | needs_review |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | I could not find this information in the available documents. | needs_review |
| g050 | simple | If my Platinum PPO claim is denied, by when must I appeal? | Appeal deadline for Platinum PPO: 120 days. | If your Platinum PPO claim is denied, you must appeal within 30 days from the date on the denial letter. | answered |
| g053 | simple | If I miss a Term 30 premium payment, how long before coverage lapses? | Premium grace period for Term 30: 15 days. | I could not find this in the available documents. | needs_review |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period of 6 hours compared to Business Traveler's 15 hours. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | The appeal deadline for Multi-Pet is 120 days, while Pet Complete does not have a specified appeal deadline, so Multi-Pet has the longer appeal deadline. | answered |
| g135 | comparison | Which has the slower claim decision time: Term 30 or Universal Life? | Universal Life (Term 30: 10 days; Universal Life: 14 days). | Term 30 has a faster claim decision time of 10 days compared to Universal Life's 14 days, so Term 30 has the slower claim decision time. | answered |
| g153 | internal | After how many claims in 12 months is a travel policyholder referred to SIU? | Siu referral trigger: 6 claims. | I could not find this information in the available documents. | needs_review |
