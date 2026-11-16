# Eval report: ablation-no-grounding

- run at: 2026-11-16T17:13:46+00:00
- cases: 89  |  judge: False  |  overrides: `{'grounding_check': False}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 89 |
| answer_accuracy | 0.8315 |
| accuracy_answerable | 0.8052 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.026 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 8 |
| by_type.amendment.accuracy | 1.0 |
| by_type.comparison.n | 12 |
| by_type.comparison.accuracy | 0.3333 |
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
| citations.relevant_rate | 0.88 |
| review.flagged_rate | 0.1798 |
| review.auto_answer_accuracy | 0.8219 |
| review.error_recall | 0.1333 |
| routing.complex.share | 0.2809 |
| routing.complex.accuracy | 0.68 |
| routing.complex.latency_ms_p50 | 3184.5 |
| routing.complex.cost_usd_mean | 0.0002 |
| routing.simple.share | 0.7191 |
| routing.simple.accuracy | 0.8906 |
| routing.simple.latency_ms_p50 | 2661.9 |
| routing.simple.cost_usd_mean | 0.0001 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2719.9 |
| latency_ms_p95 | 3297.5 |
| llm_ms_p50 | 2636.1 |
| retrieval_ms_p50 | 90.0 |
| tokens_in_mean | 1132.1 |
| tokens_out_mean | 91.9 |
| cost_per_query_usd | 0.00017282 |
| cost_per_1k_queries_usd | 0.1728 |
| internal_leaks | 0 |

## Gate: FAIL

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.8315 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.8052 | 0.8 | ✅ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9805 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 0.9888 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.8219 | 0.9 | ❌ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3297.5 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.8315 | 0.8311 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.8052 | 0.8087 | ❌ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9805 | 0.9603 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9372 | 0.8973 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.8219 | 0.8623 | ❌ |
| review.error_recall | drop <= 0.1 vs baseline | 0.1333 | 0.34 | ❌ |
| latency_ms_p95 | <= 1.3x baseline | 3297.5 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00017282 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g005 | simple | Within how many days will Velmora Assurance decide a complete Annual Multi-Trip claim? | Claim decision time for Annual Multi-Trip: 15 days. | 10 days | answered |
| g040 | simple | If my Silver PPO claim is denied, by when must I appeal? | Appeal deadline for Silver PPO: 30 days. | You must file a written appeal within 90 days of the denial notice for Silver PPO. | answered |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | You have 120 days from the date of the denial notice to file a written appeal for a denied Fleet Commercial claim. | answered |
| g065 | simple | How many days' notice will I get before my Whole Life coverage is cancelled? | Cancellation notice period for Whole Life: 60 days. | 20 days | answered |
| g070 | simple | How long do I have to file a claim under Whole Life? | Claim filing deadline for Whole Life: 365 days. | You have 45 days to file a complete Whole Life claim from the date of receipt of the claim, with a timeline pausing if additional information is needed. For par | answered |
| g074 | simple | How long do I have to appeal a denied Standard Auto claim? | Appeal deadline for Standard Auto: 120 days. | You have 180 days to file a written appeal for a denied Trip Standard claim, and 90 days for a denied Renters Essential claim. | answered |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | I could not find this in the available documents. | needs_review |
| g123 | comparison | Which has the higher water backup sublimit: Condo Shield or HomeBasic? | HomeBasic (Condo Shield: $7,500; HomeBasic: $25,000). | Condo Shield has the higher water backup sublimit: $7,500 for Condo Shield versus $25,000 for HomeBasic. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g128 | comparison | Between the Pet Accident Only and Pet Wellness plans, which one has a faster claim decision time? | Pet Wellness (Pet Accident Only: 21 days; Pet Wellness: 15 days). | Pet Accident Only has a faster claim decision time: 21 days for Pet Accident Only versus 15 days for Pet Wellness. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has a 7 days waiting period for illnesses from the policy start date, while Multi-Pet has a 10 days waiting period. The appeal deadlines are not di | needs_review |
| g132 | comparison | Which has the shorter premium grace period: Rideshare Auto or Basic Liability? | Basic Liability (Rideshare Auto: 30 days; Basic Liability: 20 days). | Rideshare Auto has a 30-day grace period, while Basic Liability has a 20-day grace period. | answered |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Both Bronze HMO and Silver PPO have the same coinsurance rate of 30% after the deductible for covered in-network services. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | HomeStandard has a faster claim decision time: 10 days for HomeStandard versus no specific time mentioned for HomePlus. | answered |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days after the loss occurs for Exotic Pet versus 21 days for Pet Accident Only. | answered |
