"""Verifiable math rewards used by the GRPO example."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Sequence

RewardFunction = Callable[..., List[float]]


def _completion_text(completion: Any) -> str:
    """Accept both plain completions and conversational TRL completions."""
    if isinstance(completion, str):
        return completion
    if isinstance(completion, dict):
        return str(completion.get("content", ""))
    if isinstance(completion, Sequence) and not isinstance(completion, (bytes, str)):
        parts = [_completion_text(item) for item in completion]
        return "\n".join(part for part in parts if part)
    return str(completion)


class MathRewardFunction:
    """Return 1 for a numerically correct answer and 0 otherwise."""

    def __init__(self, tolerance: float = 1e-4) -> None:
        if tolerance < 0:
            raise ValueError("tolerance cannot be negative")
        self.tolerance = tolerance
        self.__name__ = type(self).__name__

    @staticmethod
    def extract_answer(text: str) -> Optional[str]:
        patterns = (
            r"Final Answer:\s*([^\n]+)",
            r"####\s*([^\n]+)",
            r"答案(?:是)?\s*[:：]?\s*([^\n]+)",
            r"Therefore,?\s*(?:the answer is)?\s*([^\n]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        numbers = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        return numbers[-1] if numbers else None

    @staticmethod
    def normalize_answer(answer: Optional[str]) -> Optional[float]:
        if answer is None:
            return None
        normalized = (
            answer.replace(",", "")
            .replace("$", "")
            .replace("%", "")
            .strip()
        )
        match = re.search(r"-?\d+(?:\.\d+)?", normalized)
        if match is None:
            return None
        try:
            value = float(match.group(0))
        except ValueError:
            return None
        return value

    def compare_answers(self, prediction: str, truth: str) -> bool:
        predicted_number = self.normalize_answer(prediction)
        truth_number = self.normalize_answer(truth)
        if predicted_number is not None and truth_number is not None:
            return abs(predicted_number - truth_number) <= self.tolerance
        return prediction.strip().casefold() == truth.strip().casefold()

    def __call__(
        self,
        completions: Sequence[Any],
        ground_truth: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> List[float]:
        truths = ground_truth or kwargs.get("ground_truth") or kwargs.get(
            "ground_truths"
        )
        if truths is None:
            raise ValueError("ground_truth must be provided")
        if len(completions) != len(truths):
            raise ValueError("completions and ground_truth must have equal length")

        rewards: List[float] = []
        for completion, truth in zip(completions, truths):
            answer = self.extract_answer(_completion_text(completion))
            correct = answer is not None and self.compare_answers(answer, str(truth))
            rewards.append(1.0 if correct else 0.0)
        return rewards


class AccuracyReward(MathRewardFunction):
    """Semantic name used by the four-layer architecture in the article."""


class LengthPenaltyReward:
    """Penalize only the part of a completion beyond the configured limit."""

    def __init__(
        self,
        base_reward_fn: RewardFunction,
        max_length: int = 1024,
        penalty_weight: float = 0.1,
    ) -> None:
        if max_length <= 0 or penalty_weight < 0:
            raise ValueError("invalid length-penalty configuration")
        self.base_reward_fn = base_reward_fn
        self.max_length = max_length
        self.penalty_weight = penalty_weight
        self.__name__ = type(self).__name__

    def __call__(self, completions: Sequence[Any], **kwargs: Any) -> List[float]:
        rewards = self.base_reward_fn(completions, **kwargs)
        adjusted = []
        for reward, completion in zip(rewards, completions):
            overflow = max(0, len(_completion_text(completion)) - self.max_length)
            penalty = self.penalty_weight * overflow / self.max_length
            adjusted.append(max(0.0, reward - penalty))
        return adjusted


class StepReward:
    """Add a capped bonus for explicit non-empty reasoning lines."""

    def __init__(
        self,
        base_reward_fn: RewardFunction,
        step_bonus: float = 0.1,
        max_bonus: float = 0.5,
    ) -> None:
        if step_bonus < 0 or max_bonus < 0:
            raise ValueError("step rewards cannot be negative")
        self.base_reward_fn = base_reward_fn
        self.step_bonus = step_bonus
        self.max_bonus = max_bonus
        self.__name__ = type(self).__name__

    def __call__(self, completions: Sequence[Any], **kwargs: Any) -> List[float]:
        rewards = self.base_reward_fn(completions, **kwargs)
        result = []
        for reward, completion in zip(rewards, completions):
            lines = [
                line for line in _completion_text(completion).splitlines() if line.strip()
            ]
            bonus = min(self.step_bonus * max(0, len(lines) - 1), self.max_bonus)
            result.append(reward + bonus)
        return result


def create_accuracy_reward(tolerance: float = 1e-4) -> AccuracyReward:
    return AccuracyReward(tolerance=tolerance)


def create_length_penalty_reward(
    base_reward_fn: RewardFunction,
    max_length: int = 1024,
    penalty_weight: float = 0.1,
) -> LengthPenaltyReward:
    return LengthPenaltyReward(base_reward_fn, max_length, penalty_weight)


def create_step_reward(
    base_reward_fn: RewardFunction,
    step_bonus: float = 0.1,
) -> StepReward:
    return StepReward(base_reward_fn, step_bonus)


def evaluate_rewards(
    completions: Sequence[Any],
    ground_truths: Sequence[str],
    reward_fn: RewardFunction,
) -> Dict[str, Any]:
    rewards = reward_fn(completions, ground_truth=ground_truths)
    return {
        "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
        "max_reward": max(rewards) if rewards else 0.0,
        "min_reward": min(rewards) if rewards else 0.0,
        "accuracy": (
            sum(reward > 0.5 for reward in rewards) / len(rewards)
            if rewards
            else 0.0
        ),
        "num_samples": len(rewards),
    }
