# Eval report: ablation-no-rerank

- run at: 2026-11-16T16:51:02+00:00
- cases: 89  |  judge: False  |  overrides: `{'rerank': False}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 89 |
| answer_accuracy | 0.764 |
| accuracy_answerable | 0.7273 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.013 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 8 |
| by_type.amendment.accuracy | 0.5 |
| by_type.comparison.n | 12 |
| by_type.comparison.accuracy | 0.1667 |
| by_type.internal.n | 5 |
| by_type.internal.accuracy | 1.0 |
| by_type.simple.n | 52 |
| by_type.simple.accuracy | 0.8654 |
| by_type.unanswerable.n | 12 |
| by_type.unanswerable.accuracy | 1.0 |
| retrieval.hit_rate | 0.9481 |
| retrieval.context_recall | 0.9286 |
| retrieval.mrr | 0.8381 |
| retrieval.context_precision | 0.8345 |
| faithfulness | None |
| answer_relevancy | None |
| format.valid_rate | 1.0 |
| format.valid_first_try_rate | 1.0 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 1.0 |
| citations.relevant_rate | 0.7895 |
| review.flagged_rate | 0.3034 |
| review.auto_answer_accuracy | 0.7742 |
| review.error_recall | 0.3333 |
| routing.complex.share | 0.1348 |
| routing.complex.accuracy | 0.1667 |
| routing.complex.latency_ms_p50 | 3193.6 |
| routing.complex.cost_usd_mean | 0.0003 |
| routing.simple.share | 0.8652 |
| routing.simple.accuracy | 0.8571 |
| routing.simple.latency_ms_p50 | 2606.7 |
| routing.simple.cost_usd_mean | 0.0001 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2620.4 |
| latency_ms_p95 | 3215.5 |
| llm_ms_p50 | 2608.7 |
| retrieval_ms_p50 | 10.7 |
| tokens_in_mean | 1116.1 |
| tokens_out_mean | 92.0 |
| cost_per_query_usd | 0.00015973 |
| cost_per_1k_queries_usd | 0.1597 |
| internal_leaks | 0 |

## Gate: FAIL

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.764 | 0.8 | ❌ |
| accuracy_answerable | >= floor | 0.7273 | 0.8 | ❌ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 0.9481 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9286 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 1.0 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.7742 | 0.9 | ❌ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3215.5 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.764 | 0.8311 | ❌ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.7273 | 0.8087 | ❌ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 0.9481 | 0.97 | ❌ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9286 | 0.9603 | ❌ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.8381 | 0.8973 | ❌ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.7742 | 0.8623 | ❌ |
| review.error_recall | drop <= 0.1 vs baseline | 0.3333 | 0.34 | ❌ |
| latency_ms_p95 | <= 1.3x baseline | 3215.5 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00015973 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g028 | simple | What is the maximum enrollment age for Pet Complete? | Maximum enrollment age for Pet Complete: 10 years. | 14 years | needs_review |
| g040 | simple | If my Silver PPO claim is denied, by when must I appeal? | Appeal deadline for Silver PPO: 30 days. | If your Silver PPO claim is denied, you must file a written appeal within 90 days of the denial notice. | needs_review |
| g041 | simple | How many days of grace period does Basic Liability allow for missed payments? | Premium grace period for Basic Liability: 20 days. | 10 days before cancellation for missed payments on Basic Liability policy. | answered |
| g073 | simple | How much notice does Velmora Assurance give before cancelling a Term 30 policy? | Cancellation notice period for Term 30: 20 days. | Velmora Assurance provides a 45 days grace period before cancelling a Term 30 policy. | needs_review |
| g074 | simple | How long do I have to appeal a denied Standard Auto claim? | Appeal deadline for Standard Auto: 120 days. | You have 180 days to file a written appeal for a denied Trip Standard claim. For Standard Auto, the filing deadline is 45 days after the loss occurs. | needs_review |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | You must file a written appeal within 90 days of the denial notice for the Bronze HMO plan. | needs_review |
| g096 | simple | How many days' notice will I get before my Term 20 coverage is cancelled? | Cancellation notice period for Term 20: 45 days. | 10 days | answered |
| g109 | amendment | How much is the all-perils deductible for HomePlus? | All-perils deductible for HomePlus: $1,500 (per the latest amendment). | $2,500 | answered |
| g112 | amendment | What deductible do I have to meet on Bronze HMO before coverage kicks in? | Annual deductible for Bronze HMO: $1,000 (per the latest amendment). | $500 | answered |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | Multi-Pet reimburses 60% of eligible veterinary costs after the deductible. | answered |
| g114 | amendment | What is the specialist copay on Silver PPO? | Specialist visit copay for Silver PPO: $50 (per the latest amendment). | $75 | answered |
| g123 | comparison | Which has the higher water backup sublimit: Condo Shield or HomeBasic? | HomeBasic (Condo Shield: $7,500; HomeBasic: $25,000). | Condo Shield has the higher water backup sublimit: $7,500 for Condo Shield versus $25,000 for HomeBasic. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g128 | comparison | Between the Pet Accident Only and Pet Wellness plans, which one has a faster claim decision time? | Pet Wellness (Pet Accident Only: 21 days; Pet Wellness: 15 days). | Both Pet Accident Only and Pet Wellness plans have the same claim decision time: you will receive a claim number by email within one business day. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has no specified appeal deadline, while Multi-Pet allows for appeals within 120 days of the denial notice. | answered |
| g132 | comparison | Which has the shorter premium grace period: Rideshare Auto or Basic Liability? | Basic Liability (Rideshare Auto: 30 days; Basic Liability: 20 days). | Rideshare Auto has a 30-day grace period for premium payments, while Basic Liability has a 20-day grace period. | answered |
| g135 | comparison | Which has the slower claim decision time: Term 30 or Universal Life? | Universal Life (Term 30: 10 days; Universal Life: 14 days). | Term 30 has a claim submission deadline of 90 days, while Universal Life has a claim submission deadline of 90 days as well. Therefore, both have the same claim | answered |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Bronze HMO has the lower coinsurance rate: 30% for Bronze HMO versus 10% for Silver PPO. | answered |
| g140 | comparison | Which has the longer claim filing deadline: Senior Pet or Pet Complete? | Senior Pet (Senior Pet: 45 days; Pet Complete: 30 days). | Pet Complete has a shorter claim filing deadline of 30 days, compared to Senior Pet's unspecified deadline, which is effectively longer. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | I could not find this in the available documents. | needs_review |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days for Exotic Pet versus 180 days for Pet Accident Only. | needs_review |
