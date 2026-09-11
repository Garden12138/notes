"""Thin, source-aligned wrappers around TRL's SFT and GRPO trainers."""

from __future__ import annotations

import inspect
import math
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Type

from .utils import TrainingConfig, require_rl_dependencies


def compute_group_advantages(
    rewards: Sequence[float],
    scale_by_std: bool = False,
    epsilon: float = 1e-4,
) -> Dict[str, Any]:
    """Compute the centered advantages used to explain one GRPO group."""
    if not rewards:
        raise ValueError("rewards cannot be empty")
    values = [float(reward) for reward in rewards]
    if not all(math.isfinite(reward) for reward in values):
        raise ValueError("rewards must contain only finite numbers")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")

    mean_reward = sum(values) / len(values)
    centered = [reward - mean_reward for reward in values]
    variance = sum(value * value for value in centered) / len(centered)
    reward_std = math.sqrt(variance)
    if scale_by_std and reward_std > 0:
        advantages = [value / (reward_std + epsilon) for value in centered]
    else:
        advantages = centered
    return {
        "mean_reward": mean_reward,
        "reward_std": reward_std,
        "advantages": advantages,
    }


def _supported_kwargs(factory: Type[Any], values: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the wrapper usable across nearby TRL argument-name changes."""
    parameters = inspect.signature(factory).parameters
    if any(item.kind is inspect.Parameter.VAR_KEYWORD for item in parameters.values()):
        return values
    return {key: value for key, value in values.items() if key in parameters}


def _processing_kwargs(factory: Type[Any], tokenizer: Any) -> Dict[str, Any]:
    """Choose the tokenizer argument used by the installed TRL release."""
    parameters = inspect.signature(factory).parameters
    if "processing_class" in parameters:
        return {"processing_class": tokenizer}
    if "tokenizer" in parameters:
        return {"tokenizer": tokenizer}
    return {}


def _warmup_kwargs(
    factory: Type[Any],
    config: TrainingConfig,
) -> Dict[str, float | int]:
    """Map ratio-based warmup across Transformers argument revisions."""
    parameters = inspect.signature(factory).parameters
    accepts_kwargs = any(
        item.kind is inspect.Parameter.VAR_KEYWORD
        for item in parameters.values()
    )
    if "warmup_ratio" in parameters or accepts_kwargs:
        return {
            "warmup_steps": config.warmup_steps,
            "warmup_ratio": config.warmup_ratio,
        }
    warmup = config.warmup_steps or config.warmup_ratio
    return {"warmup_steps": warmup}


class BaseTrainerWrapper:
    """Common model setup and persistence for chapter 11 trainers."""

    def __init__(self, config: Optional[TrainingConfig] = None) -> None:
        require_rl_dependencies()
        self.config = config or TrainingConfig()
        self.model: Any = None
        self.tokenizer: Any = None
        self.trainer: Any = None
        self.loaded_adapter = False

    def setup_model(self) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer_kwargs: Dict[str, Any] = {"trust_remote_code": True}
        model_kwargs: Dict[str, Any] = {"trust_remote_code": True}
        if self.config.model_revision:
            tokenizer_kwargs["revision"] = self.config.model_revision
            model_kwargs["revision"] = self.config.model_revision

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            **tokenizer_kwargs,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        model_path = Path(self.config.model_name).expanduser()
        adapter_config = model_path / "adapter_config.json"
        if adapter_config.is_file():
            if not self.config.use_lora:
                raise ValueError(
                    "a LoRA adapter checkpoint requires use_lora=True"
                )
            from peft import AutoPeftModelForCausalLM

            self.model = AutoPeftModelForCausalLM.from_pretrained(
                self.config.model_name,
                is_trainable=True,
                **model_kwargs,
            )
            self.loaded_adapter = True
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                **model_kwargs,
            )
        if self.config.gradient_checkpointing:
            self.model.config.use_cache = False

    def _peft_config(self) -> Any:
        if not self.config.use_lora or self.loaded_adapter:
            return None
        from peft import LoraConfig, TaskType

        return LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.lora_target_modules,
            bias="none",
        )

    def _report_to(self) -> list[str]:
        destinations = []
        if self.config.use_wandb:
            destinations.append("wandb")
        if self.config.use_tensorboard:
            destinations.append("tensorboard")
        return destinations

    def train(self) -> Any:
        raise NotImplementedError

    def parameter_summary(self) -> Dict[str, float | int]:
        """Count total and trainable parameters after PEFT wrapping."""
        model = getattr(self.trainer, "model", None)
        if model is None:
            model = self.model
        if model is None:
            raise RuntimeError("model has not been initialized")
        total = sum(parameter.numel() for parameter in model.parameters())
        trainable = sum(
            parameter.numel()
            for parameter in model.parameters()
            if parameter.requires_grad
        )
        percentage = 100.0 * trainable / total if total else 0.0
        return {
            "trainable_parameters": trainable,
            "total_parameters": total,
            "trainable_percentage": percentage,
        }

    def save_model(self, output_dir: Optional[str] = None) -> Path:
        if self.trainer is None:
            raise RuntimeError("trainer has not been initialized")
        destination = Path(output_dir or self.config.output_dir).expanduser()
        destination.mkdir(parents=True, exist_ok=True)
        self.trainer.save_model(str(destination))
        if self.tokenizer is not None:
            self.tokenizer.save_pretrained(str(destination))
        return destination


class SFTTrainerWrapper(BaseTrainerWrapper):
    """Supervised fine-tuning wrapper for prompt-completion data."""

    def __init__(
        self,
        config: Optional[TrainingConfig] = None,
        dataset: Any = None,
        eval_dataset: Any = None,
    ) -> None:
        super().__init__(config)
        self.dataset = dataset
        self.eval_dataset = eval_dataset

    def train(self) -> Any:
        from trl import SFTConfig, SFTTrainer

        if self.dataset is None:
            raise ValueError("dataset is required for SFT")
        if self.model is None:
            self.setup_model()

        config_values = {
            "output_dir": self.config.output_dir,
            "num_train_epochs": self.config.num_train_epochs,
            "per_device_train_batch_size": self.config.per_device_train_batch_size,
            "gradient_accumulation_steps": self.config.gradient_accumulation_steps,
            "learning_rate": self.config.learning_rate,
            "weight_decay": self.config.weight_decay,
            "optim": self.config.optimizer,
            "lr_scheduler_type": self.config.lr_scheduler_type,
            "logging_steps": self.config.logging_steps,
            "save_steps": self.config.save_steps,
            "fp16": self.config.use_fp16,
            "bf16": self.config.use_bf16,
            "gradient_checkpointing": self.config.gradient_checkpointing,
            "max_length": self.config.max_length,
            "max_seq_length": self.config.max_length,
            "report_to": self._report_to(),
            "seed": self.config.seed,
        }
        config_values.update(_warmup_kwargs(SFTConfig, self.config))
        sft_parameters = inspect.signature(SFTConfig).parameters
        if "completion_only_loss" in sft_parameters:
            config_values["completion_only_loss"] = True
        else:
            # Older TRL releases consume the compatibility ``text`` column.
            config_values["dataset_text_field"] = "text"
        if self.eval_dataset is not None:
            config_values.update(
                {
                    "eval_strategy": "steps",
                    "evaluation_strategy": "steps",
                    "eval_steps": self.config.eval_steps
                    or self.config.logging_steps,
                }
            )
        else:
            config_values.update(
                {"eval_strategy": "no", "evaluation_strategy": "no"}
            )
        training_args = SFTConfig(
            **_supported_kwargs(SFTConfig, config_values)
        )
        trainer_values = {
            "model": self.model,
            "args": training_args,
            "train_dataset": self.dataset,
            "eval_dataset": self.eval_dataset,
            "peft_config": self._peft_config(),
        }
        trainer_values.update(_processing_kwargs(SFTTrainer, self.tokenizer))
        self.trainer = SFTTrainer(
            **_supported_kwargs(SFTTrainer, trainer_values)
        )
        return self.trainer.train()


class GRPOTrainerWrapper(BaseTrainerWrapper):
    """Group Relative Policy Optimization with a verifiable reward."""

    def __init__(
        self,
        config: Optional[TrainingConfig] = None,
        dataset: Any = None,
        reward_fn: Optional[Callable[..., list[float]]] = None,
    ) -> None:
        super().__init__(config)
        self.dataset = dataset
        self.reward_fn = reward_fn

    def _validate_group_size(self) -> None:
        try:
            world_size = int(os.environ.get("WORLD_SIZE", "1"))
        except ValueError as exc:
            raise ValueError("WORLD_SIZE must be a positive integer") from exc
        if world_size <= 0:
            raise ValueError("WORLD_SIZE must be a positive integer")
        effective_batch = self.config.effective_batch_size * world_size
        if effective_batch % self.config.num_generations != 0:
            raise ValueError(
                "per_device_train_batch_size * gradient_accumulation_steps "
                "* WORLD_SIZE must be divisible by num_generations"
            )

    def train(self) -> Any:
        from trl import GRPOConfig, GRPOTrainer

        if self.dataset is None:
            raise ValueError("dataset is required for GRPO")
        if self.reward_fn is None:
            raise ValueError("reward_fn is required for GRPO")
        self._validate_group_size()
        if self.model is None:
            self.setup_model()

        config_values = {
            "output_dir": self.config.output_dir,
            "num_train_epochs": self.config.num_train_epochs,
            "per_device_train_batch_size": self.config.per_device_train_batch_size,
            "gradient_accumulation_steps": self.config.gradient_accumulation_steps,
            "learning_rate": self.config.learning_rate,
            "weight_decay": self.config.weight_decay,
            "optim": self.config.optimizer,
            "lr_scheduler_type": self.config.lr_scheduler_type,
            "logging_steps": self.config.logging_steps,
            "save_steps": self.config.save_steps,
            "fp16": self.config.use_fp16,
            "bf16": self.config.use_bf16,
            "gradient_checkpointing": self.config.gradient_checkpointing,
            "max_completion_length": self.config.max_completion_length,
            "num_generations": self.config.num_generations,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "beta": self.config.kl_coef,
            "epsilon": self.config.clip_range,
            "remove_unused_columns": False,
            "report_to": self._report_to(),
            "seed": self.config.seed,
        }
        config_values.update(_warmup_kwargs(GRPOConfig, self.config))
        training_args = GRPOConfig(
            **_supported_kwargs(GRPOConfig, config_values)
        )
        trainer_values = {
            "model": self.model,
            "args": training_args,
            "train_dataset": self.dataset,
            "reward_funcs": self.reward_fn,
            "peft_config": self._peft_config(),
        }
        trainer_values.update(_processing_kwargs(GRPOTrainer, self.tokenizer))
        self.trainer = GRPOTrainer(
            **_supported_kwargs(GRPOTrainer, trainer_values)
        )
        return self.trainer.train()
