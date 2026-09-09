"""Unified SFT, GRPO, dataset, reward and evaluation entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..base import Tool, ToolParameter


class RLTrainingTool(Tool):
    """Expose the dataset, reward, training and evaluation operations."""

    def __init__(self) -> None:
        super().__init__(
            name="rl_training",
            description="加载数学数据集，创建奖励函数，执行 SFT/GRPO 并评估模型",
        )
        self.custom_datasets: Dict[str, Any] = {}
        self.custom_reward_functions: Dict[str, Callable[..., List[float]]] = {}

    def register_dataset(self, name: str, dataset: Any) -> None:
        if not name.strip():
            raise ValueError("dataset name cannot be empty")
        self.custom_datasets[name] = dataset

    def register_reward_function(
        self,
        name: str,
        reward_fn: Callable[..., List[float]],
    ) -> None:
        if not name.strip() or not callable(reward_fn):
            raise ValueError("reward name and callable are required")
        self.custom_reward_functions[name] = reward_fn

    def run(self, parameters: Dict[str, Any]) -> str:
        action = str(parameters.get("action", "train")).lower()
        handlers = {
            "train": self._train,
            "load_dataset": self._load_dataset,
            "create_reward": self._create_reward,
            "evaluate": self._evaluate,
        }
        if action not in handlers:
            return self._json(
                {
                    "status": "error",
                    "message": (
                        f"不支持的操作：{action}；可选值为 "
                        "train、load_dataset、create_reward、evaluate"
                    ),
                }
            )
        try:
            return self._json(handlers[action](parameters))
        except Exception as exc:
            return self._json(
                {"status": "error", "action": action, "message": str(exc)}
            )

    def _load_dataset(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        from ...rl import create_rl_dataset, create_sft_dataset, preview_dataset

        # ``format`` is the published API. The alias keeps the chapter script usable.
        format_type = str(
            parameters.get("format", parameters.get("format_type", "sft"))
        ).lower()
        split = str(parameters.get("split", "train"))
        max_samples = self._optional_positive_int(parameters.get("max_samples", 100))
        model_name = str(parameters.get("model_name", "Qwen/Qwen3-0.6B"))
        if format_type == "sft":
            dataset = create_sft_dataset(
                max_samples=max_samples,
                split=split,
                model_name=model_name,
            )
        elif format_type == "rl":
            dataset = create_rl_dataset(
                max_samples=max_samples,
                split=split,
                model_name=model_name,
            )
        else:
            raise ValueError("format must be 'sft' or 'rl'")
        return {
            "status": "success",
            "format": format_type,
            "split": split,
            "dataset_size": len(dataset),
            "sample_keys": list(dataset.column_names),
            "preview": preview_dataset(dataset, 1),
        }

    def _create_reward(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        from ...rl import (
            create_accuracy_reward,
            create_length_penalty_reward,
            create_step_reward,
        )

        reward_type = str(parameters.get("reward_type", "accuracy")).lower()
        base_reward = create_accuracy_reward(
            float(parameters.get("tolerance", 1e-4))
        )
        details: Dict[str, Any] = {}
        if reward_type == "accuracy":
            reward_fn = base_reward
            description = "准确率奖励：答案正确为 1.0，错误为 0.0"
        elif reward_type == "length_penalty":
            details = {
                "max_length": int(parameters.get("max_length", 1024)),
                "penalty_weight": float(parameters.get("penalty_weight", 0.001)),
            }
            reward_fn = create_length_penalty_reward(base_reward, **details)
            description = (
                "长度惩罚：仅对正确但超过目标长度的回答扣分，"
                "错误答案仍为 0.0"
            )
        elif reward_type == "step":
            details = {
                "step_bonus": float(parameters.get("step_bonus", 0.1)),
                "max_steps": int(parameters.get("max_steps", 10)),
            }
            reward_fn = create_step_reward(base_reward, **details)
            description = "步骤奖励：只为答案正确的显式推理步骤加分"
        else:
            raise ValueError("reward_type must be accuracy, length_penalty or step")

        registered_name = parameters.get("register_as")
        if registered_name:
            self.register_reward_function(str(registered_name), reward_fn)
        return {
            "status": "success",
            "reward_type": reward_type,
            "description": description,
            "registered_as": registered_name,
            **details,
        }

    def _training_config(self, parameters: Dict[str, Any]) -> Any:
        from ...rl import TrainingConfig

        return TrainingConfig(
            model_name=str(parameters.get("model_name", "Qwen/Qwen3-0.6B")),
            output_dir=str(parameters.get("output_dir", "./output")),
            num_train_epochs=float(parameters.get("num_epochs", 3)),
            per_device_train_batch_size=int(parameters.get("batch_size", 4)),
            gradient_accumulation_steps=int(
                parameters.get("gradient_accumulation_steps", 4)
            ),
            learning_rate=float(parameters.get("learning_rate", 5e-5)),
            warmup_steps=int(parameters.get("warmup_steps", 100)),
            max_length=int(parameters.get("max_length", 2048)),
            max_completion_length=int(
                parameters.get("max_completion_length", 512)
            ),
            num_generations=int(parameters.get("num_generations", 8)),
            use_fp16=bool(parameters.get("use_fp16", False)),
            use_bf16=bool(parameters.get("use_bf16", False)),
            use_lora=bool(parameters.get("use_lora", True)),
            lora_r=int(parameters.get("lora_r", 16)),
            lora_alpha=int(parameters.get("lora_alpha", 32)),
            lora_dropout=float(parameters.get("lora_dropout", 0.05)),
            use_wandb=bool(parameters.get("use_wandb", False)),
            wandb_project=parameters.get("wandb_project"),
            use_tensorboard=bool(parameters.get("use_tensorboard", False)),
            seed=int(parameters.get("seed", 42)),
        )

    def _train(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        from ...rl import (
            GRPOTrainerWrapper,
            SFTTrainerWrapper,
            create_accuracy_reward,
            create_rl_dataset,
            create_sft_dataset,
            ensure_sft_text_column,
            require_rl_dependencies,
            setup_training_environment,
            validate_training_dataset,
        )

        require_rl_dependencies()
        algorithm = str(parameters.get("algorithm", "sft")).lower()
        if algorithm not in {"sft", "grpo"}:
            raise ValueError("algorithm must be 'sft' or 'grpo'")
        config = self._training_config(parameters)
        setup_training_environment(config)

        dataset_name = str(parameters.get("dataset", "gsm8k"))
        dataset = parameters.get("custom_dataset")
        if dataset is None:
            dataset = self.custom_datasets.get(dataset_name)
        if dataset is None and dataset_name.lower() != "gsm8k":
            raise ValueError(
                f"unsupported or unregistered dataset: {dataset_name}"
            )
        max_samples = self._optional_positive_int(parameters.get("max_samples"))

        if dataset is None and algorithm == "sft":
            dataset = create_sft_dataset(
                max_samples=max_samples,
                model_name=config.model_name,
            )
        elif dataset is None:
            dataset = create_rl_dataset(
                max_samples=max_samples,
                model_name=config.model_name,
            )

        if algorithm == "sft":
            dataset = ensure_sft_text_column(dataset)
            trainer = SFTTrainerWrapper(config=config, dataset=dataset)
        else:
            validate_training_dataset(dataset, "rl")
            reward = parameters.get("custom_reward")
            if isinstance(reward, str):
                reward_name = reward
                reward = self.custom_reward_functions.get(reward_name)
                if reward is None:
                    raise ValueError(
                        f"unregistered reward function: {reward_name}"
                    )
            if reward is None:
                reward = self.custom_reward_functions.get(dataset_name)
            if reward is None:
                reward = create_accuracy_reward()
            if not callable(reward):
                raise ValueError("custom_reward must be callable or registered name")
            trainer = GRPOTrainerWrapper(
                config=config,
                dataset=dataset,
                reward_fn=reward,
            )

        metrics = trainer.train()
        saved_path = trainer.save_model()
        metric_values = getattr(metrics, "metrics", {})
        return {
            "status": "success",
            "algorithm": algorithm.upper(),
            "model": config.model_name,
            "dataset_size": len(dataset),
            "output_dir": str(saved_path),
            "metrics": metric_values,
        }

    def _evaluate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        from ...rl import create_accuracy_reward, create_rl_dataset
        from ...rl.utils import require_rl_dependencies

        require_rl_dependencies()
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_path = parameters.get("model_path")
        if not model_path:
            raise ValueError("model_path is required")
        model_path = str(model_path)
        max_samples = self._optional_positive_int(
            parameters.get("max_samples", 100)
        )
        assert max_samples is not None
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        adapter_config = Path(model_path, "adapter_config.json")
        if adapter_config.exists():
            from peft import AutoPeftModelForCausalLM

            model = AutoPeftModelForCausalLM.from_pretrained(model_path)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
            )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        dataset = create_rl_dataset(
            max_samples=max_samples,
            split="test",
            model_name=model_path,
        )

        completions: List[str] = []
        truths: List[str] = []
        for row in dataset:
            encoded = tokenizer(row["prompt"], return_tensors="pt").to(device)
            with torch.no_grad():
                generated = model.generate(
                    **encoded,
                    max_new_tokens=int(parameters.get("max_new_tokens", 128)),
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                )
            prompt_length = encoded["input_ids"].shape[1]
            completions.append(
                tokenizer.decode(
                    generated[0][prompt_length:],
                    skip_special_tokens=True,
                )
            )
            truths.append(str(row["ground_truth"]))

        rewards = create_accuracy_reward()(completions, ground_truth=truths)
        accuracy = sum(rewards) / len(rewards) if rewards else 0.0
        return {
            "status": "success",
            "model_path": model_path,
            "num_samples": len(rewards),
            "accuracy": accuracy,
            "device": str(device),
        }

    @staticmethod
    def _optional_positive_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        number = int(value)
        if number <= 0:
            raise ValueError("sample count must be positive")
        return number

    @staticmethod
    def _json(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="train、load_dataset、create_reward 或 evaluate",
                required=False,
                default="train",
            ),
            ToolParameter(
                name="algorithm",
                type="string",
                description="训练算法：sft 或 grpo",
                required=False,
                default="sft",
            ),
            ToolParameter(
                name="model_name",
                type="string",
                description="Hugging Face 模型名称",
                required=False,
                default="Qwen/Qwen3-0.6B",
            ),
            ToolParameter(
                name="dataset",
                type="string",
                description="内置或已注册的数据集名称",
                required=False,
                default="gsm8k",
            ),
            ToolParameter(
                name="format",
                type="string",
                description="数据格式：sft 或 rl",
                required=False,
                default="sft",
            ),
            ToolParameter(
                name="split",
                type="string",
                description="数据集划分：train 或 test",
                required=False,
                default="train",
            ),
            ToolParameter(
                name="reward_type",
                type="string",
                description="accuracy、length_penalty 或 step",
                required=False,
                default="accuracy",
            ),
            ToolParameter(
                name="tolerance",
                type="number",
                description="数值答案比较的绝对误差容限",
                required=False,
                default=1e-4,
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="训练最大序列长度或长度奖励的目标长度",
                required=False,
                default=1024,
            ),
            ToolParameter(
                name="penalty_weight",
                type="number",
                description="超出目标长度后每个字符的惩罚权重",
                required=False,
                default=0.001,
            ),
            ToolParameter(
                name="step_bonus",
                type="number",
                description="答案正确时每个推理步骤的奖励",
                required=False,
                default=0.1,
            ),
            ToolParameter(
                name="max_steps",
                type="integer",
                description="计入奖励的最大推理步骤数",
                required=False,
                default=10,
            ),
            ToolParameter(
                name="register_as",
                type="string",
                description="保存本次创建的奖励函数所使用的注册名",
                required=False,
            ),
            ToolParameter(
                name="max_samples",
                type="integer",
                description="限制数据集样本数",
                required=False,
            ),
            ToolParameter(
                name="num_epochs",
                type="number",
                description="训练轮数",
                required=False,
                default=3,
            ),
            ToolParameter(
                name="batch_size",
                type="integer",
                description="每个设备的训练批量",
                required=False,
                default=4,
            ),
            ToolParameter(
                name="learning_rate",
                type="number",
                description="优化器学习率",
                required=False,
                default=5e-5,
            ),
            ToolParameter(
                name="num_generations",
                type="integer",
                description="GRPO 为每个 Prompt 生成的候选数",
                required=False,
                default=8,
            ),
            ToolParameter(
                name="use_lora",
                type="boolean",
                description="是否启用 LoRA",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="output_dir",
                type="string",
                description="模型与检查点输出目录",
                required=False,
                default="./output",
            ),
            ToolParameter(
                name="model_path",
                type="string",
                description="evaluate 动作加载的模型或 Adapter 路径",
                required=False,
            ),
        ]
