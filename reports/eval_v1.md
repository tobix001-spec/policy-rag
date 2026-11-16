# Eval report: v1

- run at: 2026-11-16T16:42:14+00:00
- cases: 180  |  judge: True  |  overrides: `{}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 180 |
| answer_accuracy | 0.8889 |
| accuracy_answerable | 0.871 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.0129 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 1.0 |
| by_type.comparison.n | 25 |
| by_type.comparison.accuracy | 0.8 |
| by_type.internal.n | 10 |
| by_type.internal.accuracy | 1.0 |
| by_type.simple.n | 105 |
| by_type.simple.accuracy | 0.8571 |
| by_type.unanswerable.n | 25 |
| by_type.unanswerable.accuracy | 1.0 |
| retrieval.hit_rate | 1.0 |
| retrieval.context_recall | 0.9903 |
| retrieval.mrr | 0.9473 |
| retrieval.context_precision | 0.9478 |
| faithfulness | 0.8188 |
| answer_relevancy | 0.8548 |
| format.valid_rate | 1.0 |
| format.valid_first_try_rate | 1.0 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 0.9778 |
| citations.relevant_rate | 0.8758 |
| review.flagged_rate | 0.2778 |
| review.auto_answer_accuracy | 0.9308 |
| review.error_recall | 0.55 |
| routing.complex.share | 0.2556 |
| routing.complex.accuracy | 0.8913 |
| routing.complex.latency_ms_p50 | 3361.4 |
| routing.complex.cost_usd_mean | 0.0002 |
| routing.simple.share | 0.7444 |
| routing.simple.accuracy | 0.8881 |
| routing.simple.latency_ms_p50 | 2699.7 |
| routing.simple.cost_usd_mean | 0.0001 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2736.1 |
| latency_ms_p95 | 3480.0 |
| llm_ms_p50 | 2619.9 |
| retrieval_ms_p50 | 100.4 |
| tokens_in_mean | 1135.9 |
| tokens_out_mean | 89.2 |
| cost_per_query_usd | 0.00016999 |
| cost_per_1k_queries_usd | 0.17 |
| internal_leaks | 0 |

## Gate: PASS

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.8889 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.871 | 0.8 | ✅ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9903 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 0.9778 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.9308 | 0.9 | ✅ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3480.0 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.8889 | 0.7756 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.871 | 0.7442 | ✅ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.9635 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9903 | 0.9442 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9473 | 0.8932 | ✅ |
| faithfulness | drop <= 0.05 vs baseline | 0.8188 | 0.7489 | ✅ |
| answer_relevancy | drop <= 0.05 vs baseline | 0.8548 | 0.7921 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.9308 | 0.7673 | ✅ |
| review.error_recall | drop <= 0.1 vs baseline | 0.55 | 0.0429 | ✅ |
| latency_ms_p95 | <= 1.3x baseline | 3480.0 | 4393.35 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00016999 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g002 | simple | How long do I have to appeal a denied Gold PPO claim? | Appeal deadline for Gold PPO: 45 days. | The appeal window for Gold PPO is 30 days from the date on the denial letter. | needs_review |
| g005 | simple | Within how many days will Velmora Assurance decide a complete Annual Multi-Trip claim? | Claim decision time for Annual Multi-Trip: 15 days. | Velmora Assurance issues a decision on complete Annual Multi-Trip claims within 10 days of receipt. | needs_review |
| g019 | simple | How long do I have to appeal a denied HomeBasic claim? | Appeal deadline for HomeBasic: 30 days. | For HomeBasic, you have 45 days to file a late claim after the loss occurs, and you may file a written appeal within 45 days of the denial notice. Appeals are r | answered |
| g026 | simple | How long do I have to appeal a denied Pet Accident Only claim? | Appeal deadline for Pet Accident Only: 45 days. | You have 120 days to file a written appeal for a denied Pet Accident Only claim. | needs_review |
| g039 | simple | How long do I have to appeal a denied Pet Complete claim? | Appeal deadline for Pet Complete: 60 days. | You have 30 days after the loss occurs to file a claim for Pet Complete, and if denied, you may file a written appeal within 120 days of the denial notice. Appe | needs_review |
| g040 | simple | If my Silver PPO claim is denied, by when must I appeal? | Appeal deadline for Silver PPO: 30 days. | You must file a written appeal within 90 days of the denial notice for Silver PPO. | needs_review |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | You have 120 days from the date of the denial notice to file a written appeal for a denied Fleet Commercial claim. | needs_review |
| g050 | simple | If my Platinum PPO claim is denied, by when must I appeal? | Appeal deadline for Platinum PPO: 120 days. | For Platinum PPO, the appeal window is 30 days from the date on the denial letter. | needs_review |
| g065 | simple | How many days' notice will I get before my Whole Life coverage is cancelled? | Cancellation notice period for Whole Life: 60 days. | 20 days | answered |
| g066 | simple | How many days' notice will I get before my Term 10 coverage is cancelled? | Cancellation notice period for Term 10: 30 days. | You will get 10 days' notice before your Term 10 coverage is cancelled. | answered |
| g070 | simple | How long do I have to file a claim under Whole Life? | Claim filing deadline for Whole Life: 365 days. | You have 45 days to file a complete Whole Life claim after the date of receipt, with a timeline pausing if more information is needed. For partial claims, the t | needs_review |
| g072 | simple | How much notice does Velmora Assurance give before cancelling a Exotic Pet plan? | Cancellation notice period for Exotic Pet: 20 days. | Velmora Assurance gives a 60-day grace period before cancelling the Exotic Pet plan. | answered |
| g074 | simple | How long do I have to appeal a denied Standard Auto claim? | Appeal deadline for Standard Auto: 120 days. | You have 180 days to file a written appeal for a denied Trip Standard claim, and 90 days for a denied Renters Essential claim. | needs_review |
| g076 | simple | How many failed login attempts before my account is locked? | Lockout attempts for Velmora: 5 failed attempts. | 5 | answered |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | I could not find this in the available documents. | needs_review |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has a 7 days waiting period for illnesses from the policy start date, while Multi-Pet has a 10 days waiting period. The appeal deadlines are not di | needs_review |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Both Bronze HMO and Silver PPO have the same coinsurance rate of 30% after the deductible for covered in-network services. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | HomeStandard has a faster claim decision time: 10 days for HomeStandard versus no specified time for HomePlus. | answered |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days after the loss occurs for Exotic Pet versus 21 days for Pet Accident Only. | answered |
