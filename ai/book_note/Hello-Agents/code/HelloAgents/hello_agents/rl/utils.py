"""Configuration and dependency helpers for the chapter 11 trainers."""

from __future__ import annotations

import importlib.util
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


RL_DEPENDENCIES = (
    "torch",
    "transformers",
    "datasets",
    "trl",
    "peft",
    "accelerate",
)


@dataclass
class TrainingConfig:
    """Shared configuration for SFT and GRPO training."""

    model_name: str = "Qwen/Qwen3-0.6B"
    model_revision: Optional[str] = None
    output_dir: str = "./output"
    num_train_epochs: float = 3.0
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 5e-5
    warmup_steps: int = 0
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    optimizer: str = "adamw_torch"
    lr_scheduler_type: str = "linear"
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: Optional[int] = None
    max_length: int = 2048
    max_completion_length: int = 512
    num_generations: int = 8
    temperature: float = 0.7
    top_p: float = 0.9
    kl_coef: float = 0.05
    clip_range: float = 0.2
    use_fp16: bool = False
    use_bf16: bool = False
    gradient_checkpointing: bool = True
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "v_proj"]
    )
    use_wandb: bool = False
    wandb_project: Optional[str] = None
    use_tensorboard: bool = False
    seed: int = 42

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("model_name cannot be empty")
        if self.num_train_epochs <= 0:
            raise ValueError("num_train_epochs must be greater than zero")
        if self.per_device_train_batch_size <= 0:
            raise ValueError("per_device_train_batch_size must be positive")
        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be positive")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.warmup_steps < 0:
            raise ValueError("warmup_steps cannot be negative")
        if not 0.0 <= self.warmup_ratio <= 1.0:
            raise ValueError("warmup_ratio must be between 0 and 1")
        if self.weight_decay < 0:
            raise ValueError("weight_decay cannot be negative")
        if not self.optimizer.strip() or not self.lr_scheduler_type.strip():
            raise ValueError("optimizer and lr_scheduler_type cannot be empty")
        if self.logging_steps <= 0 or self.save_steps <= 0:
            raise ValueError("logging_steps and save_steps must be positive")
        if self.eval_steps is not None and self.eval_steps <= 0:
            raise ValueError("eval_steps must be positive when provided")
        if self.max_length <= 0 or self.max_completion_length <= 0:
            raise ValueError("sequence lengths must be positive")
        if self.num_generations < 2:
            raise ValueError("num_generations must be at least 2")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive for GRPO sampling")
        if not 0.0 < self.top_p <= 1.0:
            raise ValueError("top_p must be in (0, 1]")
        if self.kl_coef < 0:
            raise ValueError("kl_coef cannot be negative")
        if not 0.0 < self.clip_range < 1.0:
            raise ValueError("clip_range must be in (0, 1)")
        if self.use_fp16 and self.use_bf16:
            raise ValueError("use_fp16 and use_bf16 cannot both be enabled")
        if self.use_lora:
            if self.lora_r <= 0 or self.lora_alpha <= 0:
                raise ValueError("lora_r and lora_alpha must be positive")
            if not 0.0 <= self.lora_dropout < 1.0:
                raise ValueError("lora_dropout must be in [0, 1)")
            if not self.lora_target_modules:
                raise ValueError("lora_target_modules cannot be empty")

    @property
    def effective_batch_size(self) -> int:
        return self.per_device_train_batch_size * self.gradient_accumulation_steps

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def missing_rl_dependencies() -> List[str]:
    """Return optional training packages that are not installed."""
    return [
        package
        for package in RL_DEPENDENCIES
        if importlib.util.find_spec(package) is None
    ]


def require_rl_dependencies() -> None:
    """Raise one actionable error before a training or dataset operation."""
    missing = missing_rl_dependencies()
    if missing:
        packages = ", ".join(missing)
        raise ImportError(
            f"缺少 Agentic-RL 依赖：{packages}。"
            "请安装 hello-agents[rl]==0.2.5，或为本地源码环境安装 "
            "torch、transformers>=4.51、datasets、trl、peft 与 accelerate。"
        )


def setup_training_environment(config: TrainingConfig) -> None:
    """Create the output directory and seed available random generators."""
    Path(config.output_dir).expanduser().mkdir(parents=True, exist_ok=True)
    random.seed(config.seed)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if config.use_wandb and config.wandb_project:
        os.environ["WANDB_PROJECT"] = config.wandb_project

    try:
        import numpy as np

        np.random.seed(config.seed)
    except ImportError:
        pass

    try:
        import torch

        torch.manual_seed(config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(config.seed)
    except ImportError:
        pass
