from typing import List, Dict

def calculate_metrics(retrieved_docs: List[str], relevant_docs: List[str]) -> Dict[str, any]:
    a = len([doc for doc in retrieved_docs if doc in relevant_docs])  # найдено и релевантно
    b = len([doc for doc in retrieved_docs if doc not in relevant_docs])  # найдено и нерелевантно
    c = len([doc for doc in relevant_docs if doc not in retrieved_docs])  # не найдено и релевантно
    d = 0  # не найдено и нерелевантно

    recall = a / (a + c) if (a + c) > 0 else 0
    precision = a / (a + b) if (a + b) > 0 else 0
    accuracy = (a + d) / (a + b + c + d) if (a + b + c + d) > 0 else 0
    error = (b + c) / (a + b + c + d) if (a + b + c + d) > 0 else 0
    f1 = 2 / (1/precision + 1/recall) if precision + recall > 0 else 0

    def precision_at_k(k_val):
        top_k = retrieved_docs[:k_val]
        rel_in_top_k = len([doc for doc in top_k if doc in relevant_docs])
        return rel_in_top_k / k_val if k_val > 0 else 0

    precision_5 = precision_at_k(5)
    precision_10 = precision_at_k(10)
    R = len(relevant_docs)
    r_precision = precision_at_k(R)

    sum_precisions = 0
    num_rel = 0
    for i, doc in enumerate(retrieved_docs, start=1):
        if doc in relevant_docs:
            num_rel += 1
            sum_precisions += num_rel / i
    avg_precision = sum_precisions / len(relevant_docs) if relevant_docs else 0

    recall_levels = [i/10 for i in range(0, 11)]
    precision_at_recall = []
    for rl in recall_levels:
        precisions = []
        num_rel_found = 0
        for i, doc in enumerate(retrieved_docs, start=1):
            if doc in relevant_docs:
                num_rel_found += 1
                p = num_rel_found / i
                r = num_rel_found / len(relevant_docs)
                if r >= rl:
                    precisions.append(p)
        precision_at_recall.append(max(precisions) if precisions else 0)

    # Модифицированный вариант (RIRES)
    precision_at_recall_rires = []
    for rl in recall_levels:
        precisions = []
        num_rel_found = 0
        for i, doc in enumerate(retrieved_docs, start=1):
            if doc in relevant_docs:
                num_rel_found += 1
                p = num_rel_found / i
                r = num_rel_found / len(relevant_docs)
                if r >= rl:
                    precisions.append(p)
        precision_at_recall_rires.append(sum(precisions)/len(precisions) if precisions else 0)

    return {
        "recall": recall,
        "precision": precision,
        "accuracy": accuracy,
        "error": error,
        "f1": f1,
        "avg_precision": avg_precision,
        "precision_5": precision_5,
        "precision_10": precision_10,
        "r_precision": r_precision,
        "11_point_trec": precision_at_recall,
        "11_point_rires": precision_at_recall_rires
    }
