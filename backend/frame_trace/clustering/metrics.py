from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from sklearn.metrics import adjusted_rand_score


def pairwise_metrics(truth: dict[str, str], predicted: dict[str, str | None]) -> dict[str, float | int]:
    ids = sorted(set(truth) & set(predicted))
    tp = fp = fn = 0
    abstained = sum(1 for item_id in ids if predicted[item_id] is None)
    for a, b in combinations(ids, 2):
        same_truth = truth[a] == truth[b]
        same_pred = predicted[a] is not None and predicted[a] == predicted[b]
        if same_truth and same_pred:
            tp += 1
        elif not same_truth and same_pred:
            fp += 1
        elif same_truth and not same_pred:
            fn += 1
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    labels_truth = [truth[i] for i in ids]
    labels_pred = [predicted[i] if predicted[i] is not None else f"__abstain_{i}" for i in ids]
    return {
        "pairwise_precision": precision,
        "pairwise_recall": recall,
        "pairwise_f1": f1,
        "adjusted_rand_index": adjusted_rand_score(labels_truth, labels_pred) if ids else 1.0,
        "abstention_rate": abstained / len(ids) if ids else 0.0,
        "false_merge_pairs": fp,
        "false_split_pairs": fn,
    }
