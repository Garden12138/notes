"""Deterministic evaluation and error-analysis helpers for chapter 11.5."""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence

from .rewards import MathRewardFunction, count_reasoning_steps


SUPPORTED_EVALUATION_METRICS = frozenset(
    {
        "accuracy",
        "accuracy_at_k",
        "numerical_error",
        "average_length",
        "average_steps",
        "inference_time",
        "format_correctness",
    }
)

ERROR_TYPES = ("计算错误", "推理错误", "理解错误", "格式错误")

_FINAL_ANSWER_PATTERN = re.compile(
    r"(?im)^\s*(?:Final\s+Answer|最终答案)\s*[:：]"
)
_EXPLICIT_STEP_PATTERN = re.compile(
    r"(?im)^\s*(?:Step\s*\d+|步骤\s*\d+|\d+[.)、])\s*[:：-]?"
)
_ARITHMETIC_PATTERN = re.compile(
    r"(?P<expression>-?\d+(?:\.\d+)?"
    r"(?:\s*[+\-*/]\s*-?\d+(?:\.\d+)?)+)"
    r"\s*=\s*(?P<result>-?\d+(?:\.\d+)?)"
)
_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def normalize_evaluation_metrics(metrics: Any = None) -> List[str]:
    """Validate metric names while preserving the caller's order."""
    if metrics is None:
        values = ["accuracy"]
    elif isinstance(metrics, str):
        values = [item.strip() for item in metrics.split(",") if item.strip()]
    elif isinstance(metrics, Sequence):
        values = [str(item).strip() for item in metrics if str(item).strip()]
    else:
        raise TypeError("metrics must be a string or a sequence of strings")
    if not values:
        raise ValueError("metrics cannot be empty")

    unknown = sorted(set(values) - SUPPORTED_EVALUATION_METRICS)
    if unknown:
        choices = ", ".join(sorted(SUPPORTED_EVALUATION_METRICS))
        raise ValueError(
            f"unsupported evaluation metrics: {', '.join(unknown)}; "
            f"available metrics: {choices}"
        )
    return list(dict.fromkeys(values))


def has_expected_format(completion: str) -> bool:
    """Check the explicit step and final-answer markers taught during SFT."""
    return bool(
        _FINAL_ANSWER_PATTERN.search(completion)
        and _EXPLICIT_STEP_PATTERN.search(completion)
    )


def count_ground_truth_steps(full_answer: str) -> int:
    """Estimate GSM8K difficulty from its annotated calculation steps."""
    annotated = len(re.findall(r"<<[^<>]+>>", full_answer))
    if annotated:
        return annotated
    reasoning = full_answer.split("####", 1)[0]
    return len([line for line in reasoning.splitlines() if line.strip()])


def numerical_absolute_error(
    prediction: str,
    ground_truth: str,
) -> Optional[float]:
    """Return an absolute numeric error, or None for an unparseable answer."""
    predicted = MathRewardFunction.normalize_answer(
        MathRewardFunction.extract_answer(prediction)
    )
    expected = MathRewardFunction.normalize_answer(str(ground_truth))
    if predicted is None or expected is None:
        return None
    return abs(predicted - expected)


def _safe_arithmetic_value(expression: str) -> float:
    node = ast.parse(expression, mode="eval").body

    def evaluate(item: ast.AST) -> float:
        if isinstance(item, ast.Constant) and isinstance(item.value, (int, float)):
            return float(item.value)
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, (ast.UAdd, ast.USub)):
            value = evaluate(item.operand)
            return value if isinstance(item.op, ast.UAdd) else -value
        if isinstance(item, ast.BinOp) and type(item.op) in _BINARY_OPERATORS:
            return _BINARY_OPERATORS[type(item.op)](
                evaluate(item.left), evaluate(item.right)
            )
        raise ValueError("unsupported arithmetic expression")

    return evaluate(node)


def contains_arithmetic_error(completion: str, tolerance: float = 1e-6) -> bool:
    """Detect internally inconsistent arithmetic equalities in a completion."""
    for match in _ARITHMETIC_PATTERN.finditer(completion.replace("×", "*")):
        try:
            calculated = _safe_arithmetic_value(match.group("expression"))
            stated = float(match.group("result"))
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            continue
        if not math.isclose(calculated, stated, abs_tol=tolerance, rel_tol=0.0):
            return True
    return False


def classify_error(completion: str) -> str:
    """Apply the chapter's rule-based four-way error diagnosis."""
    if not _FINAL_ANSWER_PATTERN.search(completion):
        return "格式错误"
    if contains_arithmetic_error(completion):
        return "计算错误"
    if _EXPLICIT_STEP_PATTERN.search(completion):
        return "推理错误"
    return "理解错误"


def _difficulty(step_count: int) -> str:
    if step_count <= 2:
        return "简单(1-2步)"
    if step_count <= 4:
        return "中等(3-4步)"
    return "困难(5+步)"


def _mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0


def evaluate_prediction_records(
    records: Sequence[Mapping[str, Any]],
    metrics: Any = None,
    k: int = 3,
    return_details: bool = False,
    tolerance: float = 1e-4,
    reward_fn: Optional[Callable[..., List[float]]] = None,
) -> Dict[str, Any]:
    """Aggregate model completions into the metrics described in section 11.5.

    Each record contains ``question``, ``predictions``, ``ground_truth`` and
    optionally ``full_answer``, ``token_lengths`` and ``inference_time``.
    The first prediction is used by single-answer metrics; up to ``k``
    predictions are used by Accuracy@K.
    """
    selected = normalize_evaluation_metrics(metrics)
    if not records:
        raise ValueError("evaluation records cannot be empty")
    if k <= 0:
        raise ValueError("k must be positive")

    scorer = MathRewardFunction(tolerance=tolerance)
    details: List[Dict[str, Any]] = []
    error_distribution = {name: 0 for name in ERROR_TYPES}
    difficulty_groups: Dict[str, List[bool]] = {
        "简单(1-2步)": [],
        "中等(3-4步)": [],
        "困难(5+步)": [],
    }

    for record in records:
        raw_predictions = record.get("predictions")
        if isinstance(raw_predictions, str):
            predictions = [raw_predictions]
        elif isinstance(raw_predictions, Sequence):
            predictions = [str(value) for value in raw_predictions]
        else:
            raise TypeError("each record must provide predictions")
        if not predictions:
            raise ValueError("predictions cannot be empty")
        if "accuracy_at_k" in selected and len(predictions) < k:
            raise ValueError(
                f"Accuracy@{k} requires at least {k} predictions per record"
            )

        ground_truth = str(record.get("ground_truth", ""))
        if not ground_truth.strip():
            raise ValueError("each record must provide ground_truth")
        candidate_correctness = [
            bool(value)
            for value in scorer(
                predictions,
                ground_truth=[ground_truth] * len(predictions),
            )
        ]
        prediction = predictions[0]
        correct = candidate_correctness[0]
        top_k_correct = any(candidate_correctness[:k])
        numeric_error = numerical_absolute_error(prediction, ground_truth)

        raw_lengths = record.get("token_lengths")
        if isinstance(raw_lengths, Sequence) and not isinstance(raw_lengths, str):
            token_lengths = [int(value) for value in raw_lengths]
        else:
            token_lengths = [len(item.split()) for item in predictions]
        if len(token_lengths) != len(predictions):
            raise ValueError("token_lengths must match predictions")
        if any(value < 0 for value in token_lengths):
            raise ValueError("token_lengths cannot contain negative values")

        full_answer = str(record.get("full_answer", ""))
        ground_truth_steps = count_ground_truth_steps(full_answer)
        difficulty = _difficulty(ground_truth_steps)
        difficulty_groups[difficulty].append(correct)
        detail: Dict[str, Any] = {
            "question": str(record.get("question", "")),
            "prediction": prediction,
            "predictions": predictions,
            "ground_truth": ground_truth,
            "correct": correct,
            "top_k_correct": top_k_correct,
            "numerical_error": numeric_error,
            "generated_tokens": token_lengths[0],
            "reasoning_steps": count_reasoning_steps(prediction),
            "format_correct": has_expected_format(prediction),
            "ground_truth_steps": ground_truth_steps,
            "difficulty": difficulty,
            "inference_time": float(record.get("inference_time", 0.0)),
        }
        if not correct:
            error_type = classify_error(prediction)
            detail["error_type"] = error_type
            error_distribution[error_type] += 1
        details.append(detail)

    num_samples = len(details)
    correct_count = sum(int(item["correct"]) for item in details)
    accuracy = correct_count / num_samples
    if reward_fn is None:
        reward_values = [float(item["correct"]) for item in details]
    else:
        reward_values = [
            float(value)
            for value in reward_fn(
                [str(item["prediction"]) for item in details],
                ground_truth=[str(item["ground_truth"]) for item in details],
            )
        ]
        if len(reward_values) != num_samples:
            raise ValueError("reward_fn must return one reward per record")
        if not all(math.isfinite(value) for value in reward_values):
            raise ValueError("reward_fn returned a non-finite reward")
    for detail, reward in zip(details, reward_values):
        detail["reward"] = reward
    result: Dict[str, Any] = {
        "num_samples": num_samples,
        "metrics": selected,
        "accuracy": accuracy,
        "average_reward": _mean(reward_values),
    }
    if "accuracy_at_k" in selected:
        result["k"] = k
        result["accuracy_at_k"] = _mean(
            float(item["top_k_correct"]) for item in details
        )
    if "numerical_error" in selected:
        numeric_errors = [
            float(item["numerical_error"])
            for item in details
            if item["numerical_error"] is not None
        ]
        result["numerical_error"] = (
            _mean(numeric_errors) if numeric_errors else None
        )
        result["numerical_error_samples"] = len(numeric_errors)
    if "average_length" in selected:
        result["average_length"] = _mean(
            float(item["generated_tokens"]) for item in details
        )
    if "average_steps" in selected:
        result["average_steps"] = _mean(
            float(item["reasoning_steps"]) for item in details
        )
    if "inference_time" in selected:
        result["average_inference_time"] = _mean(
            float(item["inference_time"]) for item in details
        )
    if "format_correctness" in selected:
        result["format_correctness"] = _mean(
            float(item["format_correct"]) for item in details
        )

    if return_details:
        errors = [item for item in details if not item["correct"]]
        error_count = len(errors)
        result["details"] = details
        result["errors"] = errors
        result["error_distribution"] = error_distribution
        result["error_percentages"] = {
            name: (count / error_count if error_count else 0.0)
            for name, count in error_distribution.items()
        }
        result["accuracy_by_difficulty"] = {
            name: {
                "num_samples": len(values),
                "accuracy": _mean(float(value) for value in values),
            }
            for name, values in difficulty_groups.items()
            if values
        }
    return result
