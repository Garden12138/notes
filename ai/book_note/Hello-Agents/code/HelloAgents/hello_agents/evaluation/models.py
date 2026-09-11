"""Shared data models for the chapter 12 evaluation system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class EvaluationCase:
    """One deterministic evaluation input and its accepted references."""

    case_id: str
    prompt: str
    expected: str | Sequence[str]
    category: str = "general"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id cannot be empty")
        if not self.prompt.strip():
            raise ValueError("prompt cannot be empty")
        if not self.category.strip():
            raise ValueError("category cannot be empty")
        if not self.references:
            raise ValueError("expected must contain at least one reference")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def references(self) -> tuple[str, ...]:
        if isinstance(self.expected, str):
            return (self.expected,)
        return tuple(str(reference) for reference in self.expected)


@dataclass(frozen=True)
class TokenUsage:
    """Token counts reported by an SDK or model gateway."""

    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("token counts cannot be negative")

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class EvaluationRecord:
    """Prediction, score, cost and failure information for one case."""

    case_id: str
    category: str
    prompt: str
    references: tuple[str, ...]
    prediction: str
    score: float
    passed: bool
    duration_seconds: float
    attempts: int = 1
    attempt_errors: tuple[str, ...] = ()
    recovered: bool = False
    error: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "prompt": self.prompt,
            "references": list(self.references),
            "prediction": self.prediction,
            "score": self.score,
            "passed": self.passed,
            "duration_seconds": self.duration_seconds,
            "attempts": self.attempts,
            "attempt_errors": list(self.attempt_errors),
            "recovered": self.recovered,
            "error": self.error,
            "token_usage": (
                self.token_usage.to_dict() if self.token_usage else None
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EvaluationReport:
    """Aggregated metrics plus auditable per-case records."""

    summary: Mapping[str, Any]
    records: tuple[EvaluationRecord, ...]

    def to_dict(self, include_records: bool = True) -> dict[str, Any]:
        result = dict(self.summary)
        if include_records:
            result["records"] = [record.to_dict() for record in self.records]
        return result
