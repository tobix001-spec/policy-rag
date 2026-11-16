# Eval report: ablation-all-small

- run at: 2026-11-16T17:18:30+00:00
- cases: 89  |  judge: False  |  overrides: `{}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 89 |
| answer_accuracy | 0.8202 |
| accuracy_answerable | 0.7922 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.013 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 8 |
| by_type.amendment.accuracy | 0.375 |
| by_type.comparison.n | 12 |
| by_type.comparison.accuracy | 0.6667 |
| by_type.internal.n | 5 |
| by_type.internal.accuracy | 1.0 |
| by_type.simple.n | 52 |
| by_type.simple.accuracy | 0.8654 |
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
| citations.relevant_rate | 0.8026 |
| review.flagged_rate | 0.2584 |
| review.auto_answer_accuracy | 0.8485 |
| review.error_recall | 0.375 |
| routing.simple.share | 1.0 |
| routing.simple.accuracy | 0.8202 |
| routing.simple.latency_ms_p50 | 2650.4 |
| routing.simple.cost_usd_mean | 0.0002 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2650.4 |
| latency_ms_p95 | 3003.0 |
| llm_ms_p50 | 2559.0 |
| retrieval_ms_p50 | 87.1 |
| tokens_in_mean | 1132.1 |
| tokens_out_mean | 93.9 |
| cost_per_query_usd | 0.00015077 |
| cost_per_1k_queries_usd | 0.1508 |
| internal_leaks | 0 |

## Gate: FAIL

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.8202 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.7922 | 0.8 | ❌ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9805 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 0.9888 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.8485 | 0.9 | ❌ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3003.0 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.8202 | 0.8589 | ❌ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.7922 | 0.841 | ❌ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9805 | 0.9603 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9372 | 0.8973 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.8485 | 0.9008 | ❌ |
| review.error_recall | drop <= 0.1 vs baseline | 0.375 | 0.45 | ❌ |
| latency_ms_p95 | <= 1.3x baseline | 3003.0 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00015077 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g005 | simple | Within how many days will Velmora Assurance decide a complete Annual Multi-Trip claim? | Claim decision time for Annual Multi-Trip: 15 days. | Velmora Assurance issues a decision on complete Annual Multi-Trip claims within 10 days of receipt. | needs_review |
| g040 | simple | If my Silver PPO claim is denied, by when must I appeal? | Appeal deadline for Silver PPO: 30 days. | You must file a written appeal within 90 days of the denial notice for Silver PPO. | needs_review |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | You have 120 days from the date of the denial notice to file a written appeal for a denied Fleet Commercial claim. | needs_review |
| g065 | simple | How many days' notice will I get before my Whole Life coverage is cancelled? | Cancellation notice period for Whole Life: 60 days. | 20 days | answered |
| g070 | simple | How long do I have to file a claim under Whole Life? | Claim filing deadline for Whole Life: 365 days. | You have 45 days to file a complete Whole Life claim from the date of receipt of the claim, with a timeline pausing if additional information is needed. For par | needs_review |
| g074 | simple | How long do I have to appeal a denied Standard Auto claim? | Appeal deadline for Standard Auto: 120 days. | You have 180 days to file a written appeal for a denied Trip Standard claim, and 90 days for a denied Renters Essential claim. For Standard Auto claims, the app | answered |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | I could not find this in the available documents. | needs_review |
| g109 | amendment | How much is the all-perils deductible for HomePlus? | All-perils deductible for HomePlus: $1,500 (per the latest amendment). | $2,500 | answered |
| g112 | amendment | What deductible do I have to meet on Bronze HMO before coverage kicks in? | Annual deductible for Bronze HMO: $1,000 (per the latest amendment). | $500 | answered |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | Multi-Pet reimburses 60% of covered vet bills after the deductible is met. | answered |
| g114 | amendment | What is the specialist copay on Silver PPO? | Specialist visit copay for Silver PPO: $50 (per the latest amendment). | $75 | answered |
| g115 | amendment | Is there an age limit to apply for Term 30? | Maximum issue age for Term 30: 39 years (per the latest amendment). | The maximum issue age for Term 30 is 65 years. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours compared to 12 hours for Business Traveler. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has the longer appeal deadline: 120 days for Pet Complete versus 10 days for Multi-Pet. | needs_review |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | HomePlus has a slower claim decision time: 10 days for HomeStandard versus 180 days for HomePlus. | answered |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Pet Accident Only has the shorter claim filing deadline: 21 days versus 30 days for Exotic Pet. | answered |
