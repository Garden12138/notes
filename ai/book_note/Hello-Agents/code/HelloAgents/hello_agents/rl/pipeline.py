"""End-to-end SFT, GRPO and evaluation pipeline from section 11.6."""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional


class PipelineStageError(RuntimeError):
    """Raised when an RLTrainingTool stage returns an error result."""


def create_default_pipeline_config() -> Dict[str, Any]:
    """Return a small but complete configuration following the article."""
    return {
        "model": {"base_model": "Qwen/Qwen3-0.6B"},
        "data": {"max_samples": 1000},
        "sft": {
            "output_dir": "./output/agentic_rl/sft_model",
            "num_epochs": 3,
            "batch_size": 8,
            "gradient_accumulation_steps": 4,
            "learning_rate": 5e-5,
            "warmup_ratio": 0.1,
            "use_lora": True,
            "lora_rank": 8,
            "lora_alpha": 16,
        },
        "grpo": {
            "output_dir": "./output/agentic_rl/grpo_model",
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 1,
            "learning_rate": 1e-6,
            "warmup_ratio": 0.1,
            "num_generations": 4,
            "max_new_tokens": 256,
            "kl_coef": 0.05,
            "clip_range": 0.2,
            "use_lora": True,
            "lora_rank": 16,
            "lora_alpha": 32,
            "reward_type": "accuracy",
        },
        "eval": {
            "max_samples": 200,
            "sft_accuracy_threshold": 0.40,
            "metrics": [
                "accuracy",
                "average_length",
                "average_steps",
                "format_correctness",
            ],
            "max_new_tokens": 256,
            "return_details": False,
            "seed": 42,
        },
        "monitoring": {
            "use_wandb": False,
            "use_tensorboard": True,
            "wandb_project": "agentic-rl-pipeline",
        },
        "results_path": "./output/agentic_rl/training_results.json",
    }


def _require_mapping(config: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = config.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"config.{name} must be an object")
    return value


def _positive_number(value: Any, name: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def _positive_int(value: Any, name: str) -> int:
    number = int(value)
    if number <= 0 or float(value) != number:
        raise ValueError(f"{name} must be a positive integer")
    return number


def validate_pipeline_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate pipeline structure without importing training dependencies."""
    if not isinstance(config, Mapping):
        raise TypeError("pipeline config must be an object")
    normalized = copy.deepcopy(dict(config))
    model = _require_mapping(normalized, "model")
    data = _require_mapping(normalized, "data")
    sft = _require_mapping(normalized, "sft")
    grpo = _require_mapping(normalized, "grpo")
    evaluation = _require_mapping(normalized, "eval")
    monitoring = normalized.get("monitoring", {})
    if not isinstance(monitoring, Mapping):
        raise ValueError("config.monitoring must be an object")

    if not str(model.get("base_model", "")).strip():
        raise ValueError("config.model.base_model cannot be empty")
    _positive_int(data.get("max_samples", 0), "config.data.max_samples")
    for stage_name, stage in (("sft", sft), ("grpo", grpo)):
        if not str(stage.get("output_dir", "")).strip():
            raise ValueError(f"config.{stage_name}.output_dir cannot be empty")
        _positive_number(
            stage.get("num_epochs", 0), f"config.{stage_name}.num_epochs"
        )
        _positive_int(
            stage.get("batch_size", 0), f"config.{stage_name}.batch_size"
        )
        _positive_int(
            stage.get("gradient_accumulation_steps", 1),
            f"config.{stage_name}.gradient_accumulation_steps",
        )
        _positive_number(
            stage.get("learning_rate", 0),
            f"config.{stage_name}.learning_rate",
        )

    num_generations = _positive_int(
        grpo.get("num_generations", 0), "config.grpo.num_generations"
    )
    if num_generations < 2:
        raise ValueError("config.grpo.num_generations must be at least 2")
    try:
        world_size = int(os.environ.get("WORLD_SIZE", "1"))
    except ValueError as exc:
        raise ValueError("WORLD_SIZE must be a positive integer") from exc
    if world_size <= 0:
        raise ValueError("WORLD_SIZE must be a positive integer")
    effective_batch = int(grpo["batch_size"]) * int(
        grpo.get("gradient_accumulation_steps", 1)
    ) * world_size
    if effective_batch % num_generations != 0:
        raise ValueError(
            "the global GRPO effective batch must be divisible by "
            "num_generations; global batch = batch_size * "
            "gradient_accumulation_steps * WORLD_SIZE"
        )

    _positive_int(
        evaluation.get("max_samples", 0), "config.eval.max_samples"
    )
    threshold = float(evaluation.get("sft_accuracy_threshold", 0.0))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("config.eval.sft_accuracy_threshold must be in [0, 1]")
    if not str(normalized.get("results_path", "")).strip():
        raise ValueError("config.results_path cannot be empty")
    if Path(str(sft["output_dir"])).expanduser().resolve() == Path(
        str(grpo["output_dir"])
    ).expanduser().resolve():
        raise ValueError("SFT and GRPO output directories must differ")
    return normalized


def load_pipeline_config(path: str | Path) -> Dict[str, Any]:
    source = Path(path).expanduser()
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return validate_pipeline_config(payload)


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _process_rank() -> int:
    try:
        return int(os.environ.get("RANK", os.environ.get("LOCAL_RANK", "0")))
    except ValueError as exc:
        raise ValueError("RANK and LOCAL_RANK must be integers") from exc


class AgenticRLPipeline:
    """Orchestrate the six executable stages shown in section 11.6."""

    STAGES = (
        "prepare_data",
        "sft_training",
        "sft_evaluation",
        "grpo_training",
        "grpo_evaluation",
        "save_results",
    )

    def __init__(
        self,
        config: Mapping[str, Any],
        tool: Any = None,
        logger: Optional[Callable[[str], None]] = print,
    ) -> None:
        self.config = validate_pipeline_config(config)
        if tool is None:
            from ..tools import RLTrainingTool

            tool = RLTrainingTool()
        self.tool = tool
        self.logger = logger
        self.results: Dict[str, Any] = {
            "status": "pending",
            "stages": {},
        }

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        tool: Any = None,
        logger: Optional[Callable[[str], None]] = print,
    ) -> "AgenticRLPipeline":
        return cls(load_pipeline_config(path), tool=tool, logger=logger)

    def log(self, message: str) -> None:
        if self.logger is not None and self.is_main_process:
            self.logger(f"[{_timestamp()}] {message}")

    @property
    def is_main_process(self) -> bool:
        return _process_rank() == 0

    def preview(self) -> Dict[str, Any]:
        grpo = self.config["grpo"]
        world_size = int(os.environ.get("WORLD_SIZE", "1"))
        return {
            "base_model": self.config["model"]["base_model"],
            "train_samples": self.config["data"]["max_samples"],
            "evaluation_samples": self.config["eval"]["max_samples"],
            "sft_accuracy_threshold": self.config["eval"].get(
                "sft_accuracy_threshold", 0.0
            ),
            "world_size": world_size,
            "grpo_effective_batch": int(grpo["batch_size"])
            * int(grpo.get("gradient_accumulation_steps", 1))
            * world_size,
            "num_generations": grpo["num_generations"],
            "stages": list(self.STAGES),
            "results_path": self.config["results_path"],
        }

    def _call_tool(self, stage: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        raw_result = self.tool.run(parameters)
        result = (
            json.loads(raw_result)
            if isinstance(raw_result, str)
            else raw_result
        )
        if not isinstance(result, dict):
            raise PipelineStageError(f"{stage} returned a non-object result")
        if result.get("status") != "success":
            message = result.get("message", "unknown error")
            raise PipelineStageError(f"{stage} failed: {message}")
        self.results["stages"][stage] = result
        return result

    def _monitoring_parameters(self) -> Dict[str, Any]:
        monitoring = self.config.get("monitoring", {})
        return {
            "use_wandb": bool(monitoring.get("use_wandb", False)),
            "use_tensorboard": bool(
                monitoring.get("use_tensorboard", False)
            ),
            "wandb_project": monitoring.get("wandb_project"),
        }

    def stage1_prepare_data(self) -> Dict[str, Any]:
        self.log("阶段 1/6：准备并检查 SFT 数据")
        result = self._call_tool(
            "prepare_data",
            {
                "action": "load_dataset",
                "format": "sft",
                "model_name": self.config["model"]["base_model"],
                "max_samples": self.config["data"]["max_samples"],
            },
        )
        quality = result.get("quality")
        if not isinstance(quality, dict) or not quality.get("is_valid", False):
            issues = quality.get("issues", []) if isinstance(quality, dict) else []
            raise PipelineStageError(f"prepare_data failed quality check: {issues}")
        return result

    def stage2_sft_training(self) -> str:
        self.log("阶段 2/6：执行 SFT")
        parameters = dict(self.config["sft"])
        parameters.update(self._monitoring_parameters())
        parameters.update(
            {
                "action": "train",
                "algorithm": "sft",
                "model_name": self.config["model"]["base_model"],
                "max_samples": self.config["data"]["max_samples"],
            }
        )
        result = self._call_tool("sft_training", parameters)
        return str(result["model_path"])

    def _evaluation_parameters(self, model_path: str) -> Dict[str, Any]:
        evaluation = dict(self.config["eval"])
        evaluation.pop("sft_accuracy_threshold", None)
        evaluation.update({"action": "evaluate", "model_path": model_path})
        return evaluation

    def stage3_sft_evaluation(self, model_path: str) -> Dict[str, Any]:
        self.log("阶段 3/6：评估 SFT Adapter")
        result = self._call_tool(
            "sft_evaluation", self._evaluation_parameters(model_path)
        )
        threshold = float(
            self.config["eval"].get("sft_accuracy_threshold", 0.0)
        )
        if float(result["accuracy"]) < threshold:
            raise PipelineStageError(
                "SFT accuracy "
                f"{float(result['accuracy']):.2%} is below the configured "
                f"threshold {threshold:.2%}; GRPO was not started"
            )
        return result

    def stage4_grpo_training(self, sft_model_path: str) -> str:
        self.log("阶段 4/6：从 SFT Adapter 继续执行 GRPO")
        parameters = dict(self.config["grpo"])
        parameters.update(self._monitoring_parameters())
        parameters.update(
            {
                "action": "train",
                "algorithm": "grpo",
                "model_name": sft_model_path,
                "max_samples": self.config["data"]["max_samples"],
            }
        )
        result = self._call_tool("grpo_training", parameters)
        return str(result["model_path"])

    def stage5_grpo_evaluation(self, model_path: str) -> Dict[str, Any]:
        self.log("阶段 5/6：评估 GRPO Adapter")
        return self._call_tool(
            "grpo_evaluation", self._evaluation_parameters(model_path)
        )

    def stage6_save_results(self) -> Path:
        self.log("阶段 6/6：保存流水线结果")
        destination = Path(self.config["results_path"]).expanduser()
        self.results["results_path"] = str(destination)
        if not self.is_main_process:
            self.results["stages"]["save_results"] = {
                "status": "skipped",
                "reason": "only rank 0 writes the shared report",
            }
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.results["stages"]["save_results"] = {
            "status": "success",
            "path": str(destination),
        }
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.results, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temporary.replace(destination)
        return destination

    def run(self) -> Dict[str, Any]:
        self.results.update({"status": "running", "started_at": _timestamp()})
        try:
            self.stage1_prepare_data()
            sft_model_path = self.stage2_sft_training()
            self.stage3_sft_evaluation(sft_model_path)
            grpo_model_path = self.stage4_grpo_training(sft_model_path)
            self.stage5_grpo_evaluation(grpo_model_path)
            self.results.update(
                {"status": "success", "finished_at": _timestamp()}
            )
            self.stage6_save_results()
            self.log("完整训练流程执行完成")
            return self.results
        except Exception as exc:
            self.results.update(
                {
                    "status": "error",
                    "finished_at": _timestamp(),
                    "message": str(exc),
                }
            )
            try:
                self.stage6_save_results()
            except Exception as save_error:
                self.results["save_error"] = str(save_error)
            raise
