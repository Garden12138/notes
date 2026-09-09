"""Reinforcement-learning components introduced in chapter 11."""

from .datasets import (
    GSM8KDataset,
    create_math_dataset,
    create_rl_dataset,
    create_sft_dataset,
    format_math_dataset,
    format_rl_sample,
    format_sft_sample,
    preview_dataset,
    split_gsm8k_answer,
)
from .rewards import (
    AccuracyReward,
    LengthPenaltyReward,
    MathRewardFunction,
    StepReward,
    create_accuracy_reward,
    create_length_penalty_reward,
    create_step_reward,
    evaluate_rewards,
)
from .trainers import GRPOTrainerWrapper, SFTTrainerWrapper
from .utils import (
    RL_DEPENDENCIES,
    TrainingConfig,
    missing_rl_dependencies,
    require_rl_dependencies,
    setup_training_environment,
)

TRL_AVAILABLE = "trl" not in missing_rl_dependencies()

__all__ = [
    "AccuracyReward",
    "GRPOTrainerWrapper",
    "GSM8KDataset",
    "LengthPenaltyReward",
    "MathRewardFunction",
    "RL_DEPENDENCIES",
    "SFTTrainerWrapper",
    "StepReward",
    "TRL_AVAILABLE",
    "TrainingConfig",
    "create_accuracy_reward",
    "create_length_penalty_reward",
    "create_math_dataset",
    "create_rl_dataset",
    "create_sft_dataset",
    "create_step_reward",
    "evaluate_rewards",
    "format_math_dataset",
    "format_rl_sample",
    "format_sft_sample",
    "missing_rl_dependencies",
    "preview_dataset",
    "require_rl_dependencies",
    "setup_training_environment",
    "split_gsm8k_answer",
]
