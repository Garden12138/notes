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
        from ...rl import (
            check_dataset_quality,
            create_rl_dataset,
            create_sft_dataset,
            preview_dataset,
        )

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
            "quality": check_dataset_quality(
                dataset,
                required_fields=(
                    ("prompt", "completion")
                    if format_type == "sft"
                    else ("prompt", "ground_truth")
                ),
            ),
        }

    def _create_reward(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        reward_fn, reward_type, description, details = self._build_reward(
            parameters
        )
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

    def _build_reward(
        self,
        parameters: Dict[str, Any],
    ) -> tuple[Callable[..., List[float]], str, str, Dict[str, Any]]:
        from ...rl import (
            create_accuracy_reward,
            create_composite_reward,
            create_length_penalty_reward,
            create_step_reward,
        )

        reward_type = str(parameters.get("reward_type", "accuracy")).lower()
        reward_config = parameters.get("reward_config") or {}
        if not isinstance(reward_config, dict):
            raise ValueError("reward_config must be an object")
        base_reward = create_accuracy_reward(
            float(reward_config.get("tolerance", parameters.get("tolerance", 1e-4)))
        )
        details: Dict[str, Any] = {}
        if reward_type == "accuracy":
            reward_fn = base_reward
            description = "准确率奖励：答案正确为 1.0，错误为 0.0"
        elif reward_type == "length_penalty":
            details = {
                "max_length": int(
                    reward_config.get(
                        "target_length",
                        reward_config.get(
                            "max_length", parameters.get("max_length", 1024)
                        ),
                    )
                ),
                "penalty_weight": float(
                    reward_config.get(
                        "penalty_weight", parameters.get("penalty_weight", 0.001)
                    )
                ),
            }
            reward_fn = create_length_penalty_reward(base_reward, **details)
            description = (
                "长度惩罚：仅对正确但超过目标长度的回答扣分，"
                "错误答案仍为 0.0"
            )
        elif reward_type == "step":
            details = {
                "step_bonus": float(
                    reward_config.get(
                        "step_bonus", parameters.get("step_bonus", 0.1)
                    )
                ),
                "max_steps": int(
                    reward_config.get("max_steps", parameters.get("max_steps", 10))
                ),
            }
            reward_fn = create_step_reward(base_reward, **details)
            description = "步骤奖励：只为答案正确的显式推理步骤加分"
        elif reward_type == "combined":
            details = self._combined_reward_config(parameters, reward_config)
            reward_fn = create_composite_reward(base_reward, **details)
            description = "组合奖励：以正确性为前提，叠加长度和步骤塑形"
        else:
            raise ValueError(
                "reward_type must be accuracy, length_penalty, step or combined"
            )
        return reward_fn, reward_type, description, details

    @staticmethod
    def _combined_reward_config(
        parameters: Dict[str, Any],
        reward_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        components = reward_config.get("components")
        if components is None:
            components = [
                {"type": "accuracy", "weight": 1.0},
                {"type": "length_penalty", "weight": 1.0},
                {"type": "step", "weight": 1.0},
            ]
        if not isinstance(components, list) or not components:
            raise ValueError("reward_config.components must be a non-empty list")

        by_type: Dict[str, Dict[str, Any]] = {}
        for component in components:
            if not isinstance(component, dict):
                raise ValueError("each reward component must be an object")
            component_type = str(component.get("type", "")).lower()
            if component_type not in {"accuracy", "length_penalty", "step"}:
                raise ValueError(f"unsupported reward component: {component_type}")
            if component_type in by_type:
                raise ValueError(f"duplicate reward component: {component_type}")
            by_type[component_type] = component

        accuracy = by_type.get("accuracy", {})
        length = by_type.get("length_penalty", {})
        step = by_type.get("step", {})
        if not accuracy:
            raise ValueError("combined reward requires an accuracy component")
        return {
            "max_length": int(
                length.get(
                    "target_length",
                    length.get("max_length", parameters.get("max_length", 1024)),
                )
            ),
            "penalty_weight": float(
                length.get(
                    "penalty_weight", parameters.get("penalty_weight", 0.001)
                )
            ),
            "step_bonus": float(
                step.get("step_bonus", parameters.get("step_bonus", 0.1))
            ),
            "max_steps": int(
                step.get("max_steps", parameters.get("max_steps", 10))
            ),
            "accuracy_weight": float(accuracy.get("weight", 0.0)),
            "length_weight": float(length.get("weight", 0.0)),
            "step_weight": float(step.get("weight", 0.0)),
        }

    def _training_config(self, parameters: Dict[str, Any]) -> Any:
        from ...rl import TrainingConfig

        optimizer = str(parameters.get("optimizer", "adamw_torch")).lower()
        if optimizer == "adamw":
            optimizer = "adamw_torch"
        target_modules = parameters.get(
            "lora_target_modules", ["q_proj", "v_proj"]
        )
        if isinstance(target_modules, str):
            target_modules = [
                item.strip() for item in target_modules.split(",") if item.strip()
            ]
        eval_steps = parameters.get("eval_steps")
        return TrainingConfig(
            model_name=str(parameters.get("model_name", "Qwen/Qwen3-0.6B")),
            model_revision=parameters.get("model_revision"),
            output_dir=str(parameters.get("output_dir", "./output")),
            num_train_epochs=float(parameters.get("num_epochs", 3)),
            per_device_train_batch_size=int(parameters.get("batch_size", 4)),
            gradient_accumulation_steps=int(
                parameters.get("gradient_accumulation_steps", 4)
            ),
            learning_rate=float(parameters.get("learning_rate", 5e-5)),
            warmup_steps=int(parameters.get("warmup_steps", 0)),
            warmup_ratio=float(parameters.get("warmup_ratio", 0.1)),
            weight_decay=float(parameters.get("weight_decay", 0.01)),
            optimizer=optimizer,
            lr_scheduler_type=str(
                parameters.get("lr_scheduler_type", "linear")
            ),
            logging_steps=int(parameters.get("logging_steps", 10)),
            save_steps=int(parameters.get("save_steps", 500)),
            eval_steps=int(eval_steps) if eval_steps is not None else None,
            max_length=int(parameters.get("max_length", 2048)),
            max_completion_length=int(
                parameters.get(
                    "max_completion_length",
                    parameters.get("max_new_tokens", 512),
                )
            ),
            num_generations=int(parameters.get("num_generations", 8)),
            temperature=float(parameters.get("temperature", 0.7)),
            top_p=float(parameters.get("top_p", 0.9)),
            kl_coef=float(
                parameters.get("kl_coef", parameters.get("beta", 0.05))
            ),
            clip_range=float(
                parameters.get("clip_range", parameters.get("epsilon", 0.2))
            ),
            use_fp16=self._as_bool(parameters.get("use_fp16", False)),
            use_bf16=self._as_bool(parameters.get("use_bf16", False)),
            gradient_checkpointing=self._as_bool(
                parameters.get("gradient_checkpointing", True)
            ),
            use_lora=self._as_bool(parameters.get("use_lora", True)),
            lora_r=int(
                parameters.get("lora_r", parameters.get("lora_rank", 16))
            ),
            lora_alpha=int(parameters.get("lora_alpha", 32)),
            lora_dropout=float(parameters.get("lora_dropout", 0.05)),
            lora_target_modules=list(target_modules),
            use_wandb=self._as_bool(parameters.get("use_wandb", False)),
            wandb_project=parameters.get("wandb_project"),
            use_tensorboard=self._as_bool(
                parameters.get("use_tensorboard", False)
            ),
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
        using_custom_dataset = dataset is not None
        if dataset is None:
            dataset = self.custom_datasets.get(dataset_name)
            using_custom_dataset = dataset is not None
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
            eval_dataset = parameters.get("custom_eval_dataset")
            eval_samples = self._optional_positive_int(
                parameters.get("eval_samples")
            )
            if eval_dataset is None and eval_samples is not None:
                if using_custom_dataset:
                    raise ValueError(
                        "custom datasets require custom_eval_dataset for "
                        "step-based evaluation"
                    )
                eval_dataset = create_sft_dataset(
                    max_samples=eval_samples,
                    split="test",
                    model_name=config.model_name,
                )
            if eval_dataset is not None:
                eval_dataset = ensure_sft_text_column(eval_dataset)
            trainer = SFTTrainerWrapper(
                config=config,
                dataset=dataset,
                eval_dataset=eval_dataset,
            )
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
            if reward is None and "reward_type" in parameters:
                reward, _, _, _ = self._build_reward(parameters)
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
        parameter_summary = trainer.parameter_summary()
        saved_path = trainer.save_model()
        metric_values = dict(getattr(metrics, "metrics", {}) or {})
        final_loss = metric_values.get("train_loss")
        result = {
            "status": "success",
            "algorithm": algorithm.upper(),
            "model": config.model_name,
            "dataset_size": len(dataset),
            "num_samples": len(dataset),
            "num_epochs": config.num_train_epochs,
            "output_dir": str(saved_path),
            "model_path": str(saved_path),
            "final_loss": final_loss,
            **parameter_summary,
            "metrics": metric_values,
        }
        if algorithm == "grpo":
            result.update(
                {
                    "average_reward": self._latest_training_metric(
                        trainer,
                        metric_values,
                        "reward",
                        "train_reward",
                    ),
                    "kl": self._latest_training_metric(
                        trainer,
                        metric_values,
                        "kl",
                        "train_kl",
                    ),
                    "clip_ratio": self._latest_training_metric(
                        trainer,
                        metric_values,
                        "clip_ratio/region_mean",
                        "clip_ratio",
                    ),
                }
            )
        return result

    def _evaluate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        from ...rl import (
            create_accuracy_reward,
            create_rl_dataset,
            evaluate_prediction_records,
            normalize_evaluation_metrics,
            validate_training_dataset,
        )
        from ...rl.utils import require_rl_dependencies

        require_rl_dependencies()
        from time import perf_counter

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
        metrics = normalize_evaluation_metrics(parameters.get("metrics"))
        k = int(parameters.get("k", 3))
        if k <= 0:
            raise ValueError("k must be positive")
        generation_count = k if "accuracy_at_k" in metrics else 1
        max_new_tokens = int(parameters.get("max_new_tokens", 128))
        if max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive")
        temperature = float(parameters.get("temperature", 0.7))
        top_p = float(parameters.get("top_p", 0.9))
        if temperature <= 0 or not 0.0 < top_p <= 1.0:
            raise ValueError("temperature and top_p must be valid sampling values")
        seed = int(parameters.get("seed", 42))
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        adapter_config = Path(model_path).expanduser() / "adapter_config.json"
        if adapter_config.is_file():
            from peft import AutoPeftModelForCausalLM

            model = AutoPeftModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
            )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        dataset = parameters.get("custom_dataset")
        if dataset is None:
            dataset = create_rl_dataset(
                max_samples=max_samples,
                split="test",
                model_name=model_path,
            )
        validate_training_dataset(dataset, "rl")

        reward = parameters.get("custom_reward")
        reward_type = "custom" if reward is not None else "accuracy"
        if isinstance(reward, str):
            reward_name = reward
            reward = self.custom_reward_functions.get(reward_name)
            if reward is None:
                raise ValueError(f"unregistered reward function: {reward_name}")
            reward_type = reward_name
        if reward is None and "reward_type" in parameters:
            reward, reward_type, _, _ = self._build_reward(parameters)
        if reward is None:
            reward = create_accuracy_reward(
                float(parameters.get("tolerance", 1e-4))
            )
        if not callable(reward):
            raise ValueError("custom_reward must be callable or registered name")

        records: List[Dict[str, Any]] = []
        for row in dataset:
            encoded = tokenizer(row["prompt"], return_tensors="pt").to(device)
            generation_kwargs: Dict[str, Any] = {
                "max_new_tokens": max_new_tokens,
                "do_sample": generation_count > 1,
                "num_return_sequences": generation_count,
                "pad_token_id": tokenizer.pad_token_id,
            }
            if generation_count > 1:
                generation_kwargs.update(
                    {"temperature": temperature, "top_p": top_p}
                )
            started = perf_counter()
            with torch.no_grad():
                generated = model.generate(**encoded, **generation_kwargs)
            inference_time = perf_counter() - started
            prompt_length = encoded["input_ids"].shape[1]
            predictions = []
            token_lengths = []
            for sequence in generated:
                completion_ids = self._completion_token_ids(
                    sequence[prompt_length:],
                    tokenizer.eos_token_id,
                    tokenizer.pad_token_id,
                )
                token_lengths.append(len(completion_ids))
                predictions.append(
                    tokenizer.decode(
                        completion_ids,
                        skip_special_tokens=True,
                    )
                )
            records.append(
                {
                    "question": str(row["question"]),
                    "predictions": predictions,
                    "ground_truth": str(row["ground_truth"]),
                    "full_answer": str(row["full_answer"]),
                    "token_lengths": token_lengths,
                    "inference_time": inference_time,
                }
            )

        report = evaluate_prediction_records(
            records,
            metrics=metrics,
            k=k,
            return_details=self._as_bool(
                parameters.get("return_details", False)
            ),
            tolerance=float(parameters.get("tolerance", 1e-4)),
            reward_fn=reward,
        )
        return {
            "status": "success",
            "model_path": model_path,
            "device": str(device),
            "reward_type": reward_type,
            "generation_config": {
                "num_return_sequences": generation_count,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature if generation_count > 1 else None,
                "top_p": top_p if generation_count > 1 else None,
                "seed": seed,
            },
            **report,
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
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off", ""}:
                return False
            raise ValueError(f"invalid boolean value: {value}")
        return bool(value)

    @staticmethod
    def _completion_token_ids(
        token_ids: Any,
        eos_token_id: Any,
        pad_token_id: Any,
    ) -> List[int]:
        """Remove generated padding while retaining one terminal EOS token."""
        values = token_ids.tolist() if hasattr(token_ids, "tolist") else list(token_ids)
        result: List[int] = []
        for value in values:
            token_id = int(value)
            if pad_token_id is not None and token_id == int(pad_token_id):
                if eos_token_id is not None and token_id == int(eos_token_id):
                    result.append(token_id)
                break
            result.append(token_id)
            if eos_token_id is not None and token_id == int(eos_token_id):
                break
        return result

    @staticmethod
    def _latest_training_metric(
        trainer_wrapper: Any,
        final_metrics: Dict[str, Any],
        *names: str,
    ) -> Optional[float]:
        sources = [final_metrics]
        trainer = getattr(trainer_wrapper, "trainer", None)
        state = getattr(trainer, "state", None)
        history = getattr(state, "log_history", None) or []
        sources.extend(reversed(history))
        for source in sources:
            if not isinstance(source, dict):
                continue
            for name in names:
                value = source.get(name)
                if isinstance(value, (int, float)):
                    return float(value)
        return None

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
                description="accuracy、length_penalty、step 或 combined",
                required=False,
                default="accuracy",
            ),
            ToolParameter(
                name="reward_config",
                type="object",
                description="奖励参数；combined 可通过 components 配置组成与权重",
                required=False,
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
                name="gradient_accumulation_steps",
                type="integer",
                description="累计多少个微批次后更新一次参数",
                required=False,
                default=4,
            ),
            ToolParameter(
                name="warmup_ratio",
                type="number",
                description="学习率预热占总训练步数的比例",
                required=False,
                default=0.1,
            ),
            ToolParameter(
                name="warmup_steps",
                type="integer",
                description="固定预热步数；大于 0 时优先于 warmup_ratio",
                required=False,
                default=0,
            ),
            ToolParameter(
                name="weight_decay",
                type="number",
                description="AdamW 权重衰减系数",
                required=False,
                default=0.01,
            ),
            ToolParameter(
                name="optimizer",
                type="string",
                description="Transformers 优化器名称；adamw 会映射为 adamw_torch",
                required=False,
                default="adamw_torch",
            ),
            ToolParameter(
                name="logging_steps",
                type="integer",
                description="训练指标记录间隔",
                required=False,
                default=10,
            ),
            ToolParameter(
                name="save_steps",
                type="integer",
                description="检查点保存间隔",
                required=False,
                default=500,
            ),
            ToolParameter(
                name="eval_steps",
                type="integer",
                description="提供验证集后执行验证的步数间隔",
                required=False,
            ),
            ToolParameter(
                name="eval_samples",
                type="integer",
                description="SFT 训练中从 GSM8K test 划分加载的验证样本数",
                required=False,
            ),
            ToolParameter(
                name="max_new_tokens",
                type="integer",
                description="GRPO 训练或模型评估时最多生成的 Token 数",
                required=False,
                default=512,
            ),
            ToolParameter(
                name="num_generations",
                type="integer",
                description="GRPO 为每个 Prompt 生成的候选数",
                required=False,
                default=8,
            ),
            ToolParameter(
                name="temperature",
                type="number",
                description="GRPO 或 Accuracy@K 评估的采样温度",
                required=False,
                default=0.7,
            ),
            ToolParameter(
                name="top_p",
                type="number",
                description="GRPO 或 Accuracy@K 的 nucleus sampling 阈值",
                required=False,
                default=0.9,
            ),
            ToolParameter(
                name="kl_coef",
                type="number",
                description="GRPO 的 KL 惩罚系数，对应 TRL 的 beta",
                required=False,
                default=0.05,
            ),
            ToolParameter(
                name="clip_range",
                type="number",
                description="策略概率比裁剪范围，对应 TRL 的 epsilon",
                required=False,
                default=0.2,
            ),
            ToolParameter(
                name="use_lora",
                type="boolean",
                description="是否启用 LoRA",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="lora_rank",
                type="integer",
                description="LoRA 秩；本地配置名 lora_r 仍可作为别名",
                required=False,
                default=16,
            ),
            ToolParameter(
                name="lora_alpha",
                type="integer",
                description="LoRA 缩放系数",
                required=False,
                default=32,
            ),
            ToolParameter(
                name="lora_dropout",
                type="number",
                description="LoRA 分支的 Dropout 比例",
                required=False,
                default=0.05,
            ),
            ToolParameter(
                name="lora_target_modules",
                type="array",
                description="应用 LoRA 的线性层名称",
                required=False,
                default=["q_proj", "v_proj"],
            ),
            ToolParameter(
                name="use_wandb",
                type="boolean",
                description="是否将训练指标写入 Weights & Biases",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="wandb_project",
                type="string",
                description="Weights & Biases 项目名",
                required=False,
            ),
            ToolParameter(
                name="use_tensorboard",
                type="boolean",
                description="是否将训练指标写入 TensorBoard",
                required=False,
                default=False,
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
            ToolParameter(
                name="metrics",
                type="array",
                description=(
                    "评估指标：accuracy、accuracy_at_k、numerical_error、"
                    "average_length、average_steps、inference_time、"
                    "format_correctness"
                ),
                required=False,
                default=["accuracy"],
            ),
            ToolParameter(
                name="k",
                type="integer",
                description="Accuracy@K 为每个问题采样的候选数",
                required=False,
                default=3,
            ),
            ToolParameter(
                name="return_details",
                type="boolean",
                description="是否返回逐题结果、错误分布和难度分组",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="seed",
                type="integer",
                description="模型生成与采样的随机种子",
                required=False,
                default=42,
            ),
        ]
