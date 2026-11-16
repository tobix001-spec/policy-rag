# Eval report: ablation-all-large

- run at: 2026-11-16T17:23:23+00:00
- cases: 89  |  judge: False  |  overrides: `{}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 89 |
| answer_accuracy | 0.8989 |
| accuracy_answerable | 0.8831 |
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
| by_type.simple.accuracy | 0.9231 |
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
| citations.relevant_rate | 0.9868 |
| review.flagged_rate | 0.191 |
| review.auto_answer_accuracy | 0.9167 |
| review.error_recall | 0.3333 |
| routing.complex.share | 1.0 |
| routing.complex.accuracy | 0.8989 |
| routing.complex.latency_ms_p50 | 3032.5 |
| routing.complex.cost_usd_mean | 0.0002 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 3032.5 |
| latency_ms_p95 | 3380.4 |
| llm_ms_p50 | 2941.1 |
| retrieval_ms_p50 | 86.2 |
| tokens_in_mean | 1132.1 |
| tokens_out_mean | 84.0 |
| cost_per_query_usd | 0.00022023 |
| cost_per_1k_queries_usd | 0.2202 |
| internal_leaks | 0 |

## Gate: FAIL

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.8989 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.8831 | 0.8 | ✅ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9805 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 0.9888 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.9167 | 0.9 | ✅ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3380.4 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.8989 | 0.8589 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.8831 | 0.841 | ✅ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9805 | 0.9603 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9372 | 0.8973 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.9167 | 0.9008 | ✅ |
| review.error_recall | drop <= 0.1 vs baseline | 0.3333 | 0.45 | ❌ |
| latency_ms_p95 | <= 1.3x baseline | 3380.4 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00022023 | 0.0002 | ❌ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g019 | simple | How long do I have to appeal a denied HomeBasic claim? | Appeal deadline for HomeBasic: 30 days. | You have 45 days to appeal a denied HomeBasic claim. | needs_review |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | You have 120 days to appeal a denied Fleet Commercial claim. | needs_review |
| g096 | simple | How many days' notice will I get before my Term 20 coverage is cancelled? | Cancellation notice period for Term 20: 45 days. | Term 20 policyholders receive a 10 days grace period before coverage lapses for non-payment. | answered |
| g103 | simple | How many days' notice will I get before my Business Traveler coverage is cancelled? | Cancellation notice period for Business Traveler: 30 days. | Business Traveler policyholders receive a 10 days grace period before coverage lapses for non-payment. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has a 7 days waiting period for illnesses from the policy start date, while Multi-Pet has a 10 days waiting period. The appeal deadlines are not di | needs_review |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Both Bronze HMO and Silver PPO have the same coinsurance rate of 30% after the deductible for covered in-network services. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | HomeStandard has a faster claim decision time: 10 days for HomeStandard versus no specific time mentioned for HomePlus. | answered |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days for Exotic Pet versus 21 days for Pet Accident Only. | answered |
