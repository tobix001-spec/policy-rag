# Eval report: ablation-k2

- run at: 2026-11-16T16:59:52+00:00
- cases: 89  |  judge: False  |  overrides: `{'final_k': 2}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 89 |
| answer_accuracy | 0.8989 |
| accuracy_answerable | 0.8831 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.039 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 8 |
| by_type.amendment.accuracy | 0.875 |
| by_type.comparison.n | 12 |
| by_type.comparison.accuracy | 0.5833 |
| by_type.internal.n | 5 |
| by_type.internal.accuracy | 1.0 |
| by_type.simple.n | 52 |
| by_type.simple.accuracy | 0.9423 |
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
| citations.relevant_rate | 0.9865 |
| review.flagged_rate | 0.1798 |
| review.auto_answer_accuracy | 0.9178 |
| review.error_recall | 0.3333 |
| routing.complex.share | 0.2472 |
| routing.complex.accuracy | 0.7727 |
| routing.complex.latency_ms_p50 | 3161.9 |
| routing.complex.cost_usd_mean | 0.0002 |
| routing.simple.share | 0.7528 |
| routing.simple.accuracy | 0.9403 |
| routing.simple.latency_ms_p50 | 2574.1 |
| routing.simple.cost_usd_mean | 0.0001 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2596.7 |
| latency_ms_p95 | 3234.7 |
| llm_ms_p50 | 2513.2 |
| retrieval_ms_p50 | 80.6 |
| tokens_in_mean | 763.3 |
| tokens_out_mean | 85.3 |
| cost_per_query_usd | 0.00012805 |
| cost_per_1k_queries_usd | 0.1281 |
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
| review.auto_answer_accuracy | >= floor | 0.9178 | 0.9 | ✅ |
| internal_leaks | <= ceiling | 0 | 0 | ✅ |
| hallucination_rate | <= ceiling | 0.0 | 0.2 | ✅ |
| latency_ms_p95 | <= ceiling | 3234.7 | 15000 | ✅ |
| answer_accuracy | drop <= 0.03 vs baseline | 0.8989 | 0.8589 | ✅ |
| accuracy_answerable | drop <= 0.03 vs baseline | 0.8831 | 0.841 | ✅ |
| abstention_accuracy | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| retrieval.hit_rate | drop <= 0.03 vs baseline | 1.0 | 0.97 | ✅ |
| retrieval.context_recall | drop <= 0.03 vs baseline | 0.9805 | 0.9603 | ✅ |
| retrieval.mrr | drop <= 0.05 vs baseline | 0.9372 | 0.8973 | ✅ |
| format.valid_first_try_rate | drop <= 0.05 vs baseline | 1.0 | 0.95 | ✅ |
| review.auto_answer_accuracy | drop <= 0.03 vs baseline | 0.9178 | 0.9008 | ✅ |
| review.error_recall | drop <= 0.1 vs baseline | 0.3333 | 0.45 | ❌ |
| latency_ms_p95 | <= 1.3x baseline | 3234.7 | 4524.0 | ✅ |
| cost_per_query_usd | <= 1.25x baseline | 0.00012805 | 0.0002 | ✅ |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g073 | simple | How much notice does Velmora Assurance give before cancelling a Term 30 policy? | Cancellation notice period for Term 30: 20 days. | Velmora Assurance provides at least 30 days written notice before cancelling a Term 30 policy. | answered |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | I could not find this in the available documents. | needs_review |
| g101 | simple | How large can a photo be when I upload it in the Velmora app? | Upload mobile mb for Velmora: 10 MB. | I could not find this in the available documents. | needs_review |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | Multi-Pet reimburses 60% of eligible veterinary costs. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | Pet Complete has a 7 days waiting period for illnesses from the policy start date, while Multi-Pet has a 10 days waiting period. The appeal deadlines are not di | needs_review |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Both Bronze HMO and Silver PPO have the same coinsurance rate of 30% after the deductible for covered in-network services. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | HomeStandard has a faster claim decision time: 10 days for HomeStandard versus no specific time mentioned for HomePlus. | answered |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days after the loss occurs for Exotic Pet versus 21 days for Pet Accident Only. | answered |
