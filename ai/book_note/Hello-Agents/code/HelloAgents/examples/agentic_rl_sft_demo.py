"""LoRA SFT configuration and runnable training entry for chapter 11.3."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from hello_agents.rl import TrainingConfig
from hello_agents.tools import RLTrainingTool


def build_profile(name: str) -> Dict[str, Any]:
    """Return the quick or full GSM8K configuration used in the article."""
    common: Dict[str, Any] = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "learning_rate": 5e-5,
        "warmup_ratio": 0.1,
        "warmup_steps": 0,
        "weight_decay": 0.01,
        "optimizer": "adamw",
        "lr_scheduler_type": "linear",
        "use_lora": True,
        "lora_dropout": 0.05,
        "gradient_checkpointing": True,
    }
    if name == "quick":
        return {
            **common,
            "output_dir": "./output/sft_quick",
            "max_samples": 100,
            "num_epochs": 1,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "lora_rank": 8,
            "lora_alpha": 16,
            "lora_target_modules": ["q_proj", "v_proj"],
            "logging_steps": 10,
            "save_steps": 100,
        }
    if name == "full":
        return {
            **common,
            "output_dir": "./output/sft_full",
            "max_samples": None,
            "num_epochs": 3,
            "batch_size": 8,
            "gradient_accumulation_steps": 1,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
            ],
            "logging_steps": 100,
            "save_steps": 500,
            "eval_steps": 500,
            "eval_samples": 100,
        }
    raise ValueError("profile must be 'quick' or 'full'")


def validate_profile(parameters: Dict[str, Any]) -> TrainingConfig:
    """Validate the public tool parameters without loading a model."""
    return TrainingConfig(
        model_name=str(parameters["model_name"]),
        output_dir=str(parameters["output_dir"]),
        num_train_epochs=float(parameters["num_epochs"]),
        per_device_train_batch_size=int(parameters["batch_size"]),
        gradient_accumulation_steps=int(
            parameters["gradient_accumulation_steps"]
        ),
        learning_rate=float(parameters["learning_rate"]),
        warmup_steps=int(parameters["warmup_steps"]),
        warmup_ratio=float(parameters["warmup_ratio"]),
        weight_decay=float(parameters["weight_decay"]),
        optimizer="adamw_torch"
        if parameters["optimizer"] == "adamw"
        else str(parameters["optimizer"]),
        lr_scheduler_type=str(parameters["lr_scheduler_type"]),
        logging_steps=int(parameters["logging_steps"]),
        save_steps=int(parameters["save_steps"]),
        eval_steps=(
            int(parameters["eval_steps"])
            if parameters.get("eval_steps") is not None
            else None
        ),
        use_lora=bool(parameters["use_lora"]),
        lora_r=int(parameters["lora_rank"]),
        lora_alpha=int(parameters["lora_alpha"]),
        lora_dropout=float(parameters["lora_dropout"]),
        lora_target_modules=list(parameters["lora_target_modules"]),
        gradient_checkpointing=bool(parameters["gradient_checkpointing"]),
    )


def estimate_lora_parameters(
    hidden_size: int,
    rank: int,
    target_module_count: int,
) -> int:
    """Estimate adapter parameters when every target projection is square."""
    if hidden_size <= 0 or rank <= 0 or target_module_count <= 0:
        raise ValueError("LoRA estimate inputs must be positive")
    return target_module_count * rank * (hidden_size + hidden_size)


def print_preview(profile: str, parameters: Dict[str, Any]) -> None:
    config = validate_profile(parameters)
    estimate = estimate_lora_parameters(
        hidden_size=4096,
        rank=config.lora_r,
        target_module_count=len(config.lora_target_modules),
    )
    sample_count = parameters["max_samples"]
    print("=== SFT 配置预览 ===")
    print(f"profile: {profile}")
    print(f"model: {config.model_name}")
    print(f"samples: {'all' if sample_count is None else sample_count}")
    print(f"epochs: {config.num_train_epochs:g}")
    print(
        "effective_batch_size (single process): "
        f"{config.effective_batch_size}"
    )
    print(
        f"warmup: ratio={config.warmup_ratio}, "
        f"fixed_steps={config.warmup_steps}"
    )
    print(
        f"LoRA: r={config.lora_r}, alpha={config.lora_alpha}, "
        f"targets={config.lora_target_modules}"
    )
    print(
        "estimated LoRA parameters "
        f"(hidden=4096, square projections): {estimate:,}"
    )
    print(f"output_dir: {config.output_dir}")


def run_training(
    parameters: Dict[str, Any],
    evaluate_samples: Optional[int],
) -> None:
    tool = RLTrainingTool()
    result = json.loads(tool.run(parameters))
    print("\n=== SFT 训练结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") != "success":
        raise SystemExit(result.get("message", "SFT training failed"))

    if evaluate_samples is None:
        return
    evaluation = json.loads(tool.run({
        "action": "evaluate",
        "model_path": result["model_path"],
        "max_samples": evaluate_samples,
    }))
    print("\n=== GSM8K 测试集评估 ===")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
    if evaluation.get("status") != "success":
        raise SystemExit(evaluation.get("message", "evaluation failed"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter 11.3 LoRA SFT practice")
    parser.add_argument("--profile", choices=("quick", "full"), default="quick")
    parser.add_argument("--model-name")
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--run",
        action="store_true",
        help="download the model and dataset, then execute SFT",
    )
    parser.add_argument(
        "--evaluate-samples",
        type=int,
        help="evaluate this many GSM8K test samples after training",
    )
    args = parser.parse_args()

    if args.evaluate_samples is not None and args.evaluate_samples <= 0:
        parser.error("--evaluate-samples must be positive")
    parameters = build_profile(args.profile)
    if args.model_name:
        parameters["model_name"] = args.model_name
    if args.output_dir:
        parameters["output_dir"] = args.output_dir

    print_preview(args.profile, parameters)
    if args.run:
        run_training(parameters, args.evaluate_samples)
    else:
        print("training_requested: False (add --run to start training)")


if __name__ == "__main__":
    main()
