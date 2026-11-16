# Eval report: v0-baseline

- run at: 2026-11-16T16:22:50+00:00
- cases: 180  |  judge: True  |  overrides: `{'decompose_multi_entity': False, 'grounding_check': False, 'context_routing': False}`
- models: default `qwen2.5:7b`, small `qwen2.5:3b`, judge `qwen2.5:7b`

| metric | value |
|---|---|
| n | 180 |
| answer_accuracy | 0.7833 |
| accuracy_answerable | 0.7484 |
| abstention_accuracy | 1.0 |
| false_abstention_rate | 0.0194 |
| hallucination_rate | 0.0 |
| by_type.amendment.n | 15 |
| by_type.amendment.accuracy | 0.3333 |
| by_type.comparison.n | 25 |
| by_type.comparison.accuracy | 0.44 |
| by_type.internal.n | 10 |
| by_type.internal.accuracy | 1.0 |
| by_type.simple.n | 105 |
| by_type.simple.accuracy | 0.8571 |
| by_type.unanswerable.n | 25 |
| by_type.unanswerable.accuracy | 1.0 |
| retrieval.hit_rate | 0.9935 |
| retrieval.context_recall | 0.9742 |
| retrieval.mrr | 0.9432 |
| retrieval.context_precision | 0.9369 |
| faithfulness | 0.7989 |
| answer_relevancy | 0.8421 |
| format.valid_rate | 1.0 |
| format.valid_first_try_rate | 1.0 |
| format.coerced_rate | 0.0 |
| format.repaired_rate | 0.0 |
| citations.valid_rate | 0.9833 |
| citations.relevant_rate | 0.8158 |
| review.flagged_rate | 0.1778 |
| review.auto_answer_accuracy | 0.7703 |
| review.error_recall | 0.1282 |
| routing.complex.share | 0.1389 |
| routing.complex.accuracy | 0.44 |
| routing.complex.latency_ms_p50 | 3299.3 |
| routing.complex.cost_usd_mean | 0.0002 |
| routing.simple.share | 0.8611 |
| routing.simple.accuracy | 0.8387 |
| routing.simple.latency_ms_p50 | 2691.4 |
| routing.simple.cost_usd_mean | 0.0001 |
| fallback_rate | 0.0 |
| latency_ms_p50 | 2721.8 |
| latency_ms_p95 | 3379.5 |
| llm_ms_p50 | 2617.4 |
| retrieval_ms_p50 | 90.8 |
| tokens_in_mean | 1117.6 |
| tokens_out_mean | 88.8 |
| cost_per_query_usd | 0.0001579 |
| cost_per_1k_queries_usd | 0.1579 |
| internal_leaks | 0 |

## Incorrect cases

| id | type | question | expected | got | status |
|---|---|---|---|---|---|
| g002 | simple | How long do I have to appeal a denied Gold PPO claim? | Appeal deadline for Gold PPO: 45 days. | The appeal window for Gold PPO is 30 days from the date on the denial letter. | answered |
| g005 | simple | Within how many days will Velmora Assurance decide a complete Annual Multi-Trip claim? | Claim decision time for Annual Multi-Trip: 15 days. | 10 days of receipt | answered |
| g019 | simple | How long do I have to appeal a denied HomeBasic claim? | Appeal deadline for HomeBasic: 30 days. | For HomeBasic, you have 45 days to file a late claim, and if a claim is denied, you have 45 days to file a written appeal. | answered |
| g026 | simple | How long do I have to appeal a denied Pet Accident Only claim? | Appeal deadline for Pet Accident Only: 45 days. | You have 120 days to file a written appeal for a denied Pet Accident Only claim. | needs_review |
| g039 | simple | How long do I have to appeal a denied Pet Complete claim? | Appeal deadline for Pet Complete: 60 days. | You have 30 days after the loss occurs to file a claim for Pet Complete, and if denied, you may file a written appeal within 120 days of the denial notice. Appe | answered |
| g040 | simple | If my Silver PPO claim is denied, by when must I appeal? | Appeal deadline for Silver PPO: 30 days. | You must file a written appeal within 90 days of the denial notice for Silver PPO. | answered |
| g047 | simple | How long do I have to appeal a denied Fleet Commercial claim? | Appeal deadline for Fleet Commercial: 30 days. | You have 120 days from the date of the denial notice to file a written appeal for a denied Fleet Commercial claim. | answered |
| g050 | simple | If my Platinum PPO claim is denied, by when must I appeal? | Appeal deadline for Platinum PPO: 120 days. | For Platinum PPO, the appeal window is 30 days from the date on the denial letter. | answered |
| g065 | simple | How many days' notice will I get before my Whole Life coverage is cancelled? | Cancellation notice period for Whole Life: 60 days. | 20 days | answered |
| g066 | simple | How many days' notice will I get before my Term 10 coverage is cancelled? | Cancellation notice period for Term 10: 30 days. | You will get 10 days' notice before your Term 10 coverage is cancelled. | answered |
| g070 | simple | How long do I have to file a claim under Whole Life? | Claim filing deadline for Whole Life: 365 days. | You have 45 days to file a complete Whole Life claim from the date of receipt of the claim, with a timeline pausing if more information is needed. For partial c | answered |
| g072 | simple | How much notice does Velmora Assurance give before cancelling a Exotic Pet plan? | Cancellation notice period for Exotic Pet: 20 days. | Velmora Assurance gives a 60-day grace period before cancelling a Exotic Pet plan. | answered |
| g074 | simple | How long do I have to appeal a denied Standard Auto claim? | Appeal deadline for Standard Auto: 120 days. | You have 180 days to file a written appeal for a denied Trip Standard claim, and 90 days for a denied Renters Essential claim. | answered |
| g076 | simple | How many failed login attempts before my account is locked? | Lockout attempts for Velmora: 5 failed attempts. | 5 | answered |
| g092 | simple | If my Bronze HMO claim is denied, by when must I appeal? | Appeal deadline for Bronze HMO: 180 days. | I could not find this in the available documents. | needs_review |
| g107 | amendment | How much bodily injury coverage per person does Premier Auto provide? | Bodily injury liability limit for Premier Auto: $750,000 (per the latest amendment). | $500,000 per person | answered |
| g109 | amendment | How much is the all-perils deductible for HomePlus? | All-perils deductible for HomePlus: $1,500 (per the latest amendment). | $2,500 | answered |
| g110 | amendment | What is the free-look period for Term 10? | Free-look period for Term 10: 12 days (per the latest amendment). | The free-look period for Term 10 is 10 days. | answered |
| g112 | amendment | What deductible do I have to meet on Bronze HMO before coverage kicks in? | Annual deductible for Bronze HMO: $1,000 (per the latest amendment). | $500 | answered |
| g113 | amendment | What percentage of vet bills does Multi-Pet reimburse? | Reimbursement rate for Multi-Pet: 120% (per the latest amendment). | Multi-Pet reimburses 60% of covered vet bills after the deductible is met. | answered |
| g114 | amendment | What is the specialist copay on Silver PPO? | Specialist visit copay for Silver PPO: $50 (per the latest amendment). | $75 | answered |
| g115 | amendment | Is there an age limit to apply for Term 30? | Maximum issue age for Term 30: 39 years (per the latest amendment). | The maximum issue age for Term 30 is 65 years. | answered |
| g117 | amendment | Up to what amount does Trip Standard cover medical evacuation? | Medical evacuation limit for Trip Standard: $375,000 (per the latest amendment). | $500,000 | answered |
| g118 | amendment | What is the loss-of-use period under Landlord Protect? | Additional living expense period for Landlord Protect: 30 months (per the latest amendment). | The loss-of-use period under Landlord Protect is 24 months. | answered |
| g119 | amendment | What is the deductible on Renters Essential? | All-perils deductible for Renters Essential: $3,000 (per the latest amendment). | $1,500 for all-perils loss under Renters Essential policy. | answered |
| g121 | comparison | Which has the longer premium grace period: Pet Wellness or Exotic Pet? | Exotic Pet (Pet Wellness: 20 days; Exotic Pet: 60 days). | Pet Wellness has a 20 days grace period, while Exotic Pet has no specified grace period for premium payments. Therefore, Pet Wellness has the longer premium gra | answered |
| g122 | comparison | Compare the collision deductible of Classic Car and Fleet Commercial — which is higher? | Fleet Commercial (Classic Car: $550; Fleet Commercial: $1,000). | The collision deductible for Classic Car is $750, while for Fleet Commercial it is $1,000. Therefore, the Fleet Commercial collision deductible is higher. | answered |
| g123 | comparison | Which has the higher water backup sublimit: Condo Shield or HomeBasic? | HomeBasic (Condo Shield: $7,500; HomeBasic: $25,000). | Condo Shield has the higher water backup sublimit: $7,500 for Condo Shield versus $25,000 for HomeBasic. | answered |
| g126 | comparison | Between the Trip Premier and Business Traveler plans, which one has a shorter baggage delay waiting period? | Trip Premier (Trip Premier: 12 hours; Business Traveler: 15 hours). | Trip Premier has a shorter baggage delay waiting period: 6 hours for Trip Premier versus 12 hours for Business Traveler. | answered |
| g127 | comparison | Which has the lower medical evacuation limit: Trip Premier or Student Abroad? | Trip Premier (Trip Premier: $50,000; Student Abroad: $250,000). | Student Abroad has the lower medical evacuation limit: $250,000 for Student Abroad versus $50,000 for Trip Premier. | answered |
| g128 | comparison | Between the Pet Accident Only and Pet Wellness plans, which one has a faster claim decision time? | Pet Wellness (Pet Accident Only: 21 days; Pet Wellness: 15 days). | I could not find this in the available documents. | needs_review |
| g130 | comparison | Which has the longer appeal deadline: Pet Complete or Multi-Pet? | Multi-Pet (Pet Complete: 60 days; Multi-Pet: 120 days). | I could not find this in the available documents. | needs_review |
| g132 | comparison | Which has the shorter premium grace period: Rideshare Auto or Basic Liability? | Basic Liability (Rideshare Auto: 30 days; Basic Liability: 20 days). | Rideshare Auto has the shorter premium grace period: 30 days for Rideshare Auto versus no grace period mentioned for Basic Liability. | answered |
| g134 | comparison | Which has the higher annual benefit limit: Senior Pet or Pet Wellness? | Senior Pet (Senior Pet: $15,000; Pet Wellness: $5,000). | Pet Wellness has the higher annual benefit limit: $5,000 for Pet Wellness versus no annual benefit limit stated for Senior Pet. | needs_review |
| g137 | comparison | Between the Annual Multi-Trip and Student Abroad plans, which one has a shorter baggage delay waiting period? | Student Abroad (Annual Multi-Trip: 24 hours; Student Abroad: 18 hours). | Annual Multi-Trip has a shorter baggage delay waiting period: 24 hours for Annual Multi-Trip versus 18 hours for Student Abroad. | answered |
| g139 | comparison | Compare the coinsurance rate of Bronze HMO and Silver PPO — which is lower? | Silver PPO (Bronze HMO: 30%; Silver PPO: 10%). | Bronze HMO has the lower coinsurance rate: 30% for Bronze HMO versus 10% for Silver PPO. | answered |
| g140 | comparison | Which has the longer claim filing deadline: Senior Pet or Pet Complete? | Senior Pet (Senior Pet: 45 days; Pet Complete: 30 days). | Pet Complete has a longer claim filing deadline: 30 days for Pet Complete versus 14 days for Senior Pet. | answered |
| g141 | comparison | Between the HomeStandard and HomePlus policys, which one has a slower claim decision time? | HomePlus (HomeStandard: 10 days; HomePlus: 30 days). | Both HomeStandard and HomePlus have the same claim decision time of 10 days. | answered |
| g145 | comparison | Which has the shorter claim filing deadline: Exotic Pet or Pet Accident Only? | Exotic Pet (Exotic Pet: 180 days; Pet Accident Only: 365 days). | Exotic Pet has the shorter claim filing deadline: 180 days for Exotic Pet versus 21 days for Pet Accident Only. | answered |
