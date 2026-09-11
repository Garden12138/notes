"""Dependency-free baseline metrics introduced in section 12.1."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any, Iterable, Sequence

from .models import EvaluationRecord


def normalize_text(text: str) -> str:
    """Apply conservative Unicode, case and whitespace normalization."""
    normalized = unicodedata.normalize("NFKC", str(text)).casefold().strip()
    return " ".join(normalized.split())


def exact_match(prediction: str, reference: str) -> bool:
    return normalize_text(prediction) == normalize_text(reference)


def exact_match_score(prediction: str, references: Sequence[str]) -> float:
    """Return one when any accepted reference matches exactly."""
    return float(any(exact_match(prediction, item) for item in references))


def _tokens(text: str) -> list[str]:
    normalized = normalize_text(text)
    return re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", normalized)


def token_f1(prediction: str, reference: str) -> float:
    """Compute bag-of-token F1 for Latin words, numbers and Chinese chars."""
    predicted = _tokens(prediction)
    expected = _tokens(reference)
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    overlap = sum((Counter(predicted) & Counter(expected)).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(predicted)
    recall = overlap / len(expected)
    return 2 * precision * recall / (precision + recall)


def best_token_f1(prediction: str, references: Sequence[str]) -> float:
    if not references:
        raise ValueError("references cannot be empty")
    return max(token_f1(prediction, reference) for reference in references)


def _ratio(numerator: int | float, denominator: int) -> float:
    return float(numerator) / denominator if denominator else 0.0


def summarize_records(records: Iterable[EvaluationRecord]) -> dict[str, Any]:
    """Aggregate correctness, efficiency, robustness and category metrics."""
    items = list(records)
    if not items:
        raise ValueError("at least one evaluation record is required")

    total = len(items)
    passed = sum(record.passed for record in items)
    final_failures = sum(record.error is not None for record in items)
    initial_failures = sum(bool(record.attempt_errors) for record in items)
    recovered = sum(record.recovered for record in items)
    captured_usage = [
        record.token_usage for record in items if record.token_usage is not None
    ]

    categories: dict[str, dict[str, Any]] = {}
    for category in sorted({record.category for record in items}):
        group = [record for record in items if record.category == category]
        group_passed = sum(record.passed for record in group)
        categories[category] = {
            "total": len(group),
            "passed": group_passed,
            "accuracy": _ratio(group_passed, len(group)),
            "mean_score": sum(record.score for record in group) / len(group),
        }

    return {
        "total_samples": total,
        "passed_samples": passed,
        "accuracy": _ratio(passed, total),
        "mean_score": sum(record.score for record in items) / total,
        "task_error_rate": 1.0 - _ratio(passed, total),
        "execution_failures": final_failures,
        "execution_failure_rate": _ratio(final_failures, total),
        "initial_failures": initial_failures,
        "recovered_samples": recovered,
        "failure_recovery_rate": (
            _ratio(recovered, initial_failures)
            if initial_failures
            else None
        ),
        "average_response_time": (
            sum(record.duration_seconds for record in items) / total
        ),
        "token_usage": {
            "available": bool(captured_usage),
            "covered_samples": len(captured_usage),
            "input_tokens": sum(item.input_tokens for item in captured_usage),
            "output_tokens": sum(item.output_tokens for item in captured_usage),
            "total_tokens": sum(item.total_tokens for item in captured_usage),
        },
        "category_metrics": categories,
    }
