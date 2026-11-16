# Ablations (90-case stratified subset, no judge, gate vs baseline)

| variant | change | answer_accuracy | accuracy_answerable | abstention_accuracy | by_type.comparison.accuracy | by_type.amendment.accuracy | retrieval.hit_rate | retrieval.context_recall | retrieval.mrr | review.auto_answer_accuracy | review.error_recall | latency_ms_p50 | latency_ms_p95 | cost_per_1k_queries_usd | gate | failed checks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | everything on (reference) | 0.8764 | 0.8571 | 1.0 | 0.5833 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.9231 | 0.5455 | 2679.3 | 3353.3 | 0.1729 | PASS |  |
| no-rerank | skip the cross-encoder | 0.7978 | 0.7662 | 1.0 | 0.4167 | 0.5 | 0.9481 | 0.9286 | 0.8381 | 0.8226 | 0.3889 | 2620.4 | 3215.5 | 0.1597 | FAIL | answer_accuracy, accuracy_answerable, review.auto_answer_accuracy, answer_accuracy, accuracy_answerable, retrieval.hit_rate, retrieval.context_recall, retrieval.mrr, review.auto_answer_accuracy, review.error_recall |
| dense-only | FAISS only, no BM25 fusion | 0.8652 | 0.8442 | 1.0 | 0.5833 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.9206 | 0.5833 | 2715.6 | 3299.3 | 0.1752 | PASS |  |
| k2 | only 2 chunks of context | 0.8989 | 0.8831 | 1.0 | 0.5833 | 0.875 | 1.0 | 0.9805 | 0.9372 | 0.9178 | 0.3333 | 2596.7 | 3234.7 | 0.1281 | FAIL | review.error_recall |
| no-decompose | single retrieval for multi-product questions | 0.8539 | 0.8312 | 1.0 | 0.4167 | 1.0 | 0.987 | 0.9545 | 0.929 | 0.9355 | 0.6923 | 2731.7 | 3806.0 | 0.1701 | FAIL | answer_accuracy, accuracy_answerable, retrieval.context_recall |
| no-amend-expansion | don't pull superseding amendments into context | 0.8764 | 0.8571 | 1.0 | 0.5833 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.9524 | 0.7273 | 2764.2 | 3458.7 | 0.1625 | PASS |  |
| no-grounding | no deterministic grounding verifier | 0.8652 | 0.8442 | 1.0 | 0.5833 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.863 | 0.1667 | 2719.9 | 3297.5 | 0.1728 | FAIL | review.auto_answer_accuracy, review.auto_answer_accuracy, review.error_recall |
| all-small | every query to qwen2.5:3b | 0.8202 | 0.7922 | 1.0 | 0.6667 | 0.375 | 1.0 | 0.9805 | 0.9372 | 0.8485 | 0.375 | 2650.4 | 3003.0 | 0.1508 | FAIL | accuracy_answerable, review.auto_answer_accuracy, answer_accuracy, accuracy_answerable, review.auto_answer_accuracy, review.error_recall |
| all-large | every query to qwen2.5:7b | 0.8989 | 0.8831 | 1.0 | 0.5833 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.9167 | 0.3333 | 3032.5 | 3380.4 | 0.2202 | FAIL | review.error_recall, cost_per_query_usd |
