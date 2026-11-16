# Eval report: ablation-no-amend-expansion

- run at: 2026-11-16T17:09:18+00:00
- cases: 89  |  judge: False  |  overrides: `{'expand_amendments': False}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 89 |
| answer_accuracy | 0.8764 |
| accuracy_answerable | 0.8571 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.013 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 8 |
| by_type.amendment.accuracy | 1.0 |
| by_type.comparison.n | 12 |
| by_type.comparison.accuracy | 0.5833 |
| by_type.internal.n | 5 |
| by_type.internal.accuracy | 1.0 |
| by_type.simple.n | 52 |
| by_type.simple.accuracy | 0.8846 |
| by_type.unanswerable.n | 12 |
| by_type.unanswerable.accuracy | 1.0 |
| retrieval.hit_rate | 1.0 |
| retrieval.context_recall | 0.9805 |
| retrieval.mrr | 0.9372 |
| retrieval.context_precision | 0.9394 |
| faithfulness | None |
| answer_relevancy | None |
| format.valid_rate | 1.0 |
| format.valid_first_try_rate | 1.0 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 0.9888 |
| citations.relevant_rate | 0.9079 |
| review.flagged_rate | 0.2921 |
| review.auto_answer_accuracy | 0.9524 |
| review.error_recall | 0.7273 |
| routing.complex.share | 0.2809 |
| routing.complex.accuracy | 0.8 |
| routing.complex.latency_ms_p50 | 3328.2 |
| routing.complex.cost_usd_mean | 0.0002 |
| routing.simple.share | 0.7191 |
| routing.simple.accuracy | 0.9062 |
| routing.simple.latency_ms_p50 | 2694.3 |
| routing.simple.cost_usd_mean | 0.0001 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2764.2 |
| latency_ms_p95 | 3458.7 |
| llm_ms_p50 | 2673.3 |
| retrieval_ms_p50 | 89.2 |
| tokens_in_mean | 1041.2 |
| tokens_out_mean | 91.7 |
| cost_per_query_usd | 0.00016251 |
| cost_per_1k_queries_usd | 0.1625 |
| internal_leaks | 0 |

## Gate: PASS

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.8764 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.8571 | 0.8 | ✅ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9805 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 0.9888 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.9524 | 0.9 | ✅ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3458.7 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.8764 | 0.8589 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.8571 | 0.841 | ✅ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9805 | 0.9603 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9372 | 0.8973 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.9524 | 0.9008 | ✅ |
| review.error_recall | drop <= 0.1 vs baseline | 0.7273 | 0.45 | ✅ |
| latency_ms_p95 | <= 1.3x baseline | 3458.7 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00016251 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g005 | simple | Within how many days will Velmora Assurance decide a complete Annual Multi-Trip claim? | Claim decision time for Annual Multi-Trip: 15 days. | Velmora Assurance issues a decision on complete Annual Multi-Trip claims within 10 days of receipt. | needs_review |
| g040 | simple | If my Silver PPO claim is denied, by when must I appeal? | Appeal deadline for Silver PPO: 30 days. | You must file a written appeal within 90 days of the denial notice for Silver PPO. | needs_review |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | You have 120 days from the date of the denial notice to file a written appeal for a denied Fleet Commercial claim. | needs_review |
| g070 | simple | How long do I have to file a claim under Whole Life? | Claim filing deadline for Whole Life: 365 days. | You have 45 days to file a complete Whole Life claim from the date of receipt of the claim, with a timeline pausing if more information is needed. For partial c | needs_review |
| g077 | simple | What is the cancellation notice period for Fleet Commercial? | Cancellation notice period for Fleet Commercial: 60 days. | The minimum cancellation notice for Fleet Commercial is 10 days. | needs_review |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | I could not find this in the available documents. | needs_review |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has a 120 days appeal deadline, while Multi-Pet does not have a specified appeal deadline in the provided documents. | answered |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Both Bronze HMO and Silver PPO have the same coinsurance rate of 30% after the deductible for covered in-network services. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | HomeStandard has a faster claim decision time: 10 days for HomeStandard versus no specified time for HomePlus. | needs_review |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days after the loss occurs for Exotic Pet versus 21 days for Pet Accident Only. | needs_review |
