# Eval report: v2

- run at: 2026-11-16T18:02:59+00:00
- cases: 180  |  judge: True  |  overrides: `{}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 180 |
| answer_accuracy | 0.9333 |
| accuracy_answerable | 0.9226 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.0194 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 0.8667 |
| by_type.comparison.n | 25 |
| by_type.comparison.accuracy | 0.84 |
| by_type.internal.n | 10 |
| by_type.internal.accuracy | 0.9 |
| by_type.simple.n | 105 |
| by_type.simple.accuracy | 0.9524 |
| by_type.unanswerable.n | 25 |
| by_type.unanswerable.accuracy | 1.0 |
| retrieval.hit_rate | 1.0 |
| retrieval.context_recall | 0.9968 |
| retrieval.mrr | 0.9516 |
| retrieval.context_precision | 0.9478 |
| faithfulness | 0.8838 |
| answer_relevancy | 0.9242 |
| format.valid_rate | 1.0 |
| format.valid_first_try_rate | 1.0 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 0.9944 |
| citations.relevant_rate | 0.9079 |
| review.flagged_rate | 0.2389 |
| review.auto_answer_accuracy | 0.9489 |
| review.error_recall | 0.4167 |
| routing.complex.share | 0.2333 |
| routing.complex.accuracy | 0.8571 |
| routing.complex.latency_ms_p50 | 3589.6 |
| routing.complex.cost_usd_mean | 0.0003 |
| routing.simple.share | 0.7667 |
| routing.simple.accuracy | 0.9565 |
| routing.simple.latency_ms_p50 | 2749.6 |
| routing.simple.cost_usd_mean | 0.0002 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2799.8 |
| latency_ms_p95 | 3689.1 |
| llm_ms_p50 | 2705.3 |
| retrieval_ms_p50 | 97.3 |
| tokens_in_mean | 1203.7 |
| tokens_out_mean | 98.4 |
| cost_per_query_usd | 0.00018175 |
| cost_per_1k_queries_usd | 0.1817 |
| internal_leaks | 0 |

## Gate: PASS

| metric | check | value | limit | pass |
|---|---|---|---|---|
| answer_accuracy | >= floor | 0.9333 | 0.8 | ✅ |
| accuracy_answerable | >= floor | 0.9226 | 0.8 | ✅ |
| abstention_accuracy | >= floor | 1.0 | 0.8 | ✅ |
| retrieval.hit_rate | >= floor | 1.0 | 0.9 | ✅ |
| retrieval.context_recall | >= floor | 0.9968 | 0.85 | ✅ |
| format.valid_rate | >= floor | 1.0 | 0.98 | ✅ |
| citations.valid_rate | >= floor | 0.9944 | 0.9 | ✅ |
| review.auto_answer_accuracy | >= floor | 0.9489 | 0.9 | ✅ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3689.1 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.9333 | 0.8311 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.9226 | 0.8087 | ✅ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9968 | 0.9603 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9516 | 0.8973 | ✅ |
| faithfulness | drop <= 0.05 vs baseline | 0.8838 | 0.7688 | ✅ |
| answer_relevancy | drop <= 0.05 vs baseline | 0.9242 | 0.8048 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.9489 | 0.8623 | ✅ |
| review.error_recall | drop <= 0.1 vs baseline | 0.4167 | 0.34 | ✅ |
| latency_ms_p95 | <= 1.3x baseline | 3689.1 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00018175 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g019 | simple | How long do I have to appeal a denied HomeBasic claim? | Appeal deadline for HomeBasic: 30 days. | You have 75 days to appeal a denied HomeBasic claim. | needs_review |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | I could not find this information in the available documents. | needs_review |
| g050 | simple | If my Platinum PPO claim is denied, by when must I appeal? | Appeal deadline for Platinum PPO: 120 days. | If your Platinum PPO claim is denied, you must appeal within 30 days from the date on the denial letter. | answered |
| g074 | simple | How long do I have to appeal a denied Standard Auto claim? | Appeal deadline for Standard Auto: 120 days. | I could not find the specific appeal timeframe for Standard Auto claims in the available documents. The filing deadline for Standard Auto claims is 45 days afte | needs_review |
| g103 | simple | How many days' notice will I get before my Business Traveler coverage is cancelled? | Cancellation notice period for Business Traveler: 30 days. | You will get a 10 days grace period before your Business Traveler coverage is cancelled. | answered |
| g107 | amendment | How much bodily injury coverage per person does Premier Auto provide? | Bodily injury liability limit for Premier Auto: $750,000 (per the latest amendment). | The bodily injury coverage per person for the Premier Auto policy is $500,000. | answered |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | Multi-Pet reimburses 60% of eligible veterinary costs after the deductible. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period of 6 hours compared to Business Traveler's 15 hours. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Both Pet Complete and Multi-Pet have an appeal deadline of 120 days, so they have the same appeal deadline. | needs_review |
| g135 | comparison | Which has the slower claim decision time: Term 30 or Universal Life? | Universal Life (Term 30: 10 days; Universal Life: 14 days). | Term 30 has a faster claim decision time of 10 days compared to Universal Life's 14 days, so Term 30 has the slower claim decision time. | answered |
| g142 | comparison | Compare the jewelry theft limit of HomeBasic and Renters Essential — which is lower? | Renters Essential (HomeBasic: $7,500; Renters Essential: $2,500). | Both HomeBasic and Renters Essential have a limit of $2,500 for unscheduled jewelry theft, so they are equal in this regard. | answered |
| g153 | internal | After how many claims in 12 months is a travel policyholder referred to SIU? | Siu referral trigger: 6 claims. | I could not find this information in the available documents. | needs_review |
