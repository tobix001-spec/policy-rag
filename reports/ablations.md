# Ablations (90-case stratified subset, no judge, gate vs baseline v1; re-scored with winner check)

| variant | change | answer_accuracy | accuracy_answerable | abstention_accuracy | by_type.comparison.accuracy | by_type.amendment.accuracy | retrieval.hit_rate | retrieval.context_recall | retrieval.mrr | review.auto_answer_accuracy | review.error_recall | latency_ms_p50 | latency_ms_p95 | cost_per_1k_queries_usd | gate | failed checks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | everything on (reference) | 0.8427 | 0.8182 | 1.0 | 0.3333 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.8769 | 0.4286 | 2679.3 | 3353.3 | 0.1729 | FAIL | review.auto_answer_accuracy |
| no-rerank | skip the cross-encoder | 0.764 | 0.7273 | 1.0 | 0.1667 | 0.5 | 0.9481 | 0.9286 | 0.8381 | 0.7742 | 0.3333 | 2620.4 | 3215.5 | 0.1597 | FAIL | accuracy_answerable, answer_accuracy, retrieval.context_recall, retrieval.hit_rate, retrieval.mrr, review.auto_answer_accuracy, review.error_recall |
| dense-only | FAISS only, no BM25 fusion | 0.8315 | 0.8052 | 1.0 | 0.3333 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.873 | 0.4667 | 2715.6 | 3299.3 | 0.1752 | FAIL | accuracy_answerable, review.auto_answer_accuracy |
| k2 | only 2 chunks of context | 0.8652 | 0.8442 | 1.0 | 0.3333 | 0.875 | 1.0 | 0.9805 | 0.9372 | 0.8767 | 0.25 | 2596.7 | 3234.7 | 0.1281 | FAIL | review.auto_answer_accuracy, review.error_recall |
| no-decompose | single retrieval for multi-product questions | 0.8315 | 0.8052 | 1.0 | 0.25 | 1.0 | 0.987 | 0.9545 | 0.929 | 0.9032 | 0.6 | 2731.7 | 3806.0 | 0.1701 | FAIL | accuracy_answerable, retrieval.context_recall |
| no-amend-expansion | don't pull superseding amendments into context | 0.8427 | 0.8182 | 1.0 | 0.3333 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.9048 | 0.5714 | 2764.2 | 3458.7 | 0.1625 | PASS |  |
| no-grounding | no deterministic grounding verifier | 0.8315 | 0.8052 | 1.0 | 0.3333 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.8219 | 0.1333 | 2719.9 | 3297.5 | 0.1728 | FAIL | accuracy_answerable, review.auto_answer_accuracy, review.error_recall |
| all-small | every query to qwen2.5:3b | 0.7865 | 0.7532 | 1.0 | 0.4167 | 0.375 | 1.0 | 0.9805 | 0.9372 | 0.803 | 0.3158 | 2650.4 | 3003.0 | 0.1508 | FAIL | accuracy_answerable, answer_accuracy, review.auto_answer_accuracy, review.error_recall |
| all-large | every query to qwen2.5:7b | 0.8652 | 0.8442 | 1.0 | 0.3333 | 1.0 | 1.0 | 0.9805 | 0.9372 | 0.875 | 0.25 | 3032.5 | 3380.4 | 0.2202 | FAIL | cost_per_query_usd, review.auto_answer_accuracy, review.error_recall |
