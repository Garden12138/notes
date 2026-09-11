"""Metrics for the local BFCL teaching evaluator."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from .ast_matcher import best_match_statistics


def _divide(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 1.0 if numerator == 0 else 0.0
    return float(numerator) / float(denominator)


class BFCLMetrics:
    """Aggregate exact AST-style correctness and diagnostic overlaps."""

    def compute_metrics(
        self,
        results: Sequence[Mapping[str, Any]],
        category_weights: Mapping[str, float] | None = None,
    ) -> dict[str, Any]:
        if not results:
            raise ValueError("at least one BFCL result is required")

        total = len(results)
        correct = sum(bool(item.get("is_correct")) for item in results)
        category_counts: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "correct": 0}
        )
        predicted_calls = expected_calls = exact_calls = 0
        name_matches = expected_names = 0
        parameter_matches = expected_parameters = 0

        for item in results:
            category = str(item.get("category", "unknown"))
            category_counts[category]["total"] += 1
            category_counts[category]["correct"] += int(
                bool(item.get("is_correct"))
            )
            stats = best_match_statistics(
                item.get("prediction", []),
                item.get("ground_truth", []),
            )
            predicted_calls += stats["predicted_calls"]
            expected_calls += stats["expected_calls"]
            exact_calls += stats["exact_call_matches"]
            name_matches += stats["function_name_matches"]
            expected_names += stats["expected_calls"]
            parameter_matches += stats["parameter_matches"]
            expected_parameters += stats["expected_parameters"]

        category_statistics = {
            category: {
                **counts,
                "accuracy": _divide(counts["correct"], counts["total"]),
            }
            for category, counts in sorted(category_counts.items())
        }
        weighted_accuracy = self._weighted_accuracy(
            category_statistics,
            category_weights,
        )
        precision = _divide(exact_calls, predicted_calls)
        recall = _divide(exact_calls, expected_calls)
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        accuracy = correct / total
        return {
            "accuracy": accuracy,
            "overall_accuracy": accuracy,
            "ast_match_rate": accuracy,
            "error_rate": 1.0 - accuracy,
            "weighted_accuracy": weighted_accuracy,
            "function_name_accuracy": _divide(name_matches, expected_names),
            "parameter_accuracy": _divide(
                parameter_matches,
                expected_parameters,
            ),
            "call_precision": precision,
            "call_recall": recall,
            "f1_score": f1,
            "category_statistics": category_statistics,
        }

    @staticmethod
    def _weighted_accuracy(
        categories: Mapping[str, Mapping[str, Any]],
        weights: Mapping[str, float] | None,
    ) -> float:
        if weights is None:
            return sum(
                float(item["accuracy"]) for item in categories.values()
            ) / len(categories)

        missing = set(categories) - set(weights)
        unknown = set(weights) - set(categories)
        if missing or unknown:
            raise ValueError(
                f"category weights differ from results: missing={sorted(missing)}, "
                f"unknown={sorted(unknown)}"
            )
        if any(float(value) < 0 for value in weights.values()):
            raise ValueError("category weights cannot be negative")
        total_weight = sum(float(value) for value in weights.values())
        if total_weight <= 0:
            raise ValueError("category weights must sum to a positive value")
        return sum(
            float(categories[name]["accuracy"]) * float(weight)
            for name, weight in weights.items()
        ) / total_weight

