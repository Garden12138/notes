"""Metrics for the chapter-compatible GAIA evaluator."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


class GAIAMetrics:
    """Aggregate quasi-exact matches by level and reasoning steps."""

    def compute_metrics(
        self,
        results: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        if not results:
            raise ValueError("at least one GAIA result is required")

        scored = [item for item in results if item.get("exact_match") is not None]
        exact_matches = sum(bool(item["exact_match"]) for item in scored)
        partial_matches = sum(bool(item.get("partial_match")) for item in scored)
        level_metrics: dict[int, dict[str, Any]] = {}
        for level in (1, 2, 3):
            all_at_level = [
                item for item in results if int(item.get("level", 0)) == level
            ]
            scored_at_level = [
                item for item in all_at_level
                if item.get("exact_match") is not None
            ]
            correct = sum(bool(item["exact_match"]) for item in scored_at_level)
            level_metrics[level] = {
                "total": len(all_at_level),
                "scored": len(scored_at_level),
                "correct": correct,
                "accuracy": (
                    correct / len(scored_at_level) if scored_at_level else None
                ),
            }

        drop_rates = {
            "level_1_to_2": self._drop_rate(
                level_metrics[1]["accuracy"],
                level_metrics[2]["accuracy"],
            ),
            "level_2_to_3": self._drop_rate(
                level_metrics[2]["accuracy"],
                level_metrics[3]["accuracy"],
            ),
        }
        correct_with_steps = [
            int(item["reasoning_steps"])
            for item in scored
            if item.get("exact_match")
            and isinstance(item.get("reasoning_steps"), int)
            and int(item["reasoning_steps"]) >= 0
        ]
        return {
            "scored_samples": len(scored),
            "unscored_samples": len(results) - len(scored),
            "correct_samples": exact_matches,
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "exact_match_rate": (
                exact_matches / len(scored) if scored else None
            ),
            "overall_accuracy": (
                exact_matches / len(scored) if scored else None
            ),
            "partial_match_rate": (
                partial_matches / len(scored) if scored else None
            ),
            "level_metrics": level_metrics,
            "difficulty_drop_rates": drop_rates,
            "average_reasoning_steps": (
                sum(correct_with_steps) / len(correct_with_steps)
                if correct_with_steps
                else None
            ),
            "reasoning_step_coverage": (
                len(correct_with_steps) / exact_matches
                if exact_matches
                else None
            ),
            "execution_errors": sum(bool(item.get("error")) for item in results),
            "execution_error_rate": sum(
                bool(item.get("error")) for item in results
            ) / len(results),
        }

    @staticmethod
    def _drop_rate(
        easier_accuracy: float | None,
        harder_accuracy: float | None,
    ) -> float | None:
        if (
            easier_accuracy is None
            or harder_accuracy is None
            or easier_accuracy == 0
        ):
            return None
        return (easier_accuracy - harder_accuracy) / easier_accuracy
