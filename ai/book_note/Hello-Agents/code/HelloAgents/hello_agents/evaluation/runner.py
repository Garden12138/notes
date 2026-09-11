"""A small evaluator that can run any Agent-compatible predictor."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from .metrics import exact_match_score, summarize_records
from .models import (
    EvaluationCase,
    EvaluationRecord,
    EvaluationReport,
    TokenUsage,
)


Predictor = Callable[[str], str]
Scorer = Callable[[str, Sequence[str]], float]
UsageGetter = Callable[[], Optional[TokenUsage | Mapping[str, int]]]


class EvaluationRunner:
    """Run cases sequentially and preserve enough evidence for auditing."""

    def __init__(
        self,
        predictor: Predictor,
        scorer: Scorer = exact_match_score,
        pass_threshold: float = 1.0,
        max_retries: int = 0,
        usage_getter: Optional[UsageGetter] = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        if not callable(predictor) or not callable(scorer):
            raise TypeError("predictor and scorer must be callable")
        if not 0.0 <= pass_threshold <= 1.0:
            raise ValueError("pass_threshold must be in [0, 1]")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        self.predictor = predictor
        self.scorer = scorer
        self.pass_threshold = pass_threshold
        self.max_retries = max_retries
        self.usage_getter = usage_getter
        self.clock = clock

    def evaluate(self, cases: Iterable[EvaluationCase]) -> EvaluationReport:
        items = list(cases)
        if not items:
            raise ValueError("at least one evaluation case is required")
        case_ids = [case.case_id for case in items]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("evaluation case IDs must be unique")
        records = tuple(self._run_case(case) for case in items)
        return EvaluationReport(
            summary=summarize_records(records),
            records=records,
        )

    def _run_case(self, case: EvaluationCase) -> EvaluationRecord:
        prediction = ""
        error: Optional[str] = None
        attempt_errors: list[str] = []
        elapsed = 0.0
        attempts = 0

        for attempt in range(self.max_retries + 1):
            attempts = attempt + 1
            started = self.clock()
            try:
                result = self.predictor(case.prompt)
                if not isinstance(result, str):
                    raise TypeError("predictor must return a string")
                prediction = result
                error = None
                elapsed += max(0.0, self.clock() - started)
                break
            except Exception as exc:
                elapsed += max(0.0, self.clock() - started)
                error = f"{type(exc).__name__}: {exc}"
                attempt_errors.append(error)

        recovered = bool(attempt_errors) and error is None
        score = 0.0
        usage = None
        if error is None:
            score = float(self.scorer(prediction, case.references))
            if not 0.0 <= score <= 1.0:
                raise ValueError("scorer must return a value in [0, 1]")
            usage = self._read_usage()

        return EvaluationRecord(
            case_id=case.case_id,
            category=case.category,
            prompt=case.prompt,
            references=case.references,
            prediction=prediction,
            score=score,
            passed=error is None and score >= self.pass_threshold,
            duration_seconds=elapsed,
            attempts=attempts,
            attempt_errors=tuple(attempt_errors),
            recovered=recovered,
            error=error,
            token_usage=usage,
            metadata=case.metadata,
        )

    def _read_usage(self) -> Optional[TokenUsage]:
        if self.usage_getter is None:
            return None
        usage = self.usage_getter()
        if usage is None or isinstance(usage, TokenUsage):
            return usage
        return TokenUsage(
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
        )
