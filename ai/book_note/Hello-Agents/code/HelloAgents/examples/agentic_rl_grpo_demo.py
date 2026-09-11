"""GRPO configuration preview and runnable training entry for chapter 11.4."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from hello_agents.rl import TrainingConfig, compute_group_advantages
from hello_agents.tools import RLTrainingTool


def build_profile(name: str) -> Dict[str, Any]:
    """Return the quick or full GRPO configuration from the article."""
    common: Dict[str, Any] = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "./output/sft_full",
        "num_epochs": 3,
        "batch_size": 4,
        "gradient_accumulation_steps": 1,
        "learning_rate": 1e-5,
        "warmup_ratio": 0.1,
        "warmup_steps": 0,
        "num_generations": 4,
        "kl_coef": 0.05,
        "clip_range": 0.2,
        "use_lora": True,
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "lora_target_modules": ["q_proj", "v_proj"],
    }
    if name == "quick":
        return {
            **common,
            "output_dir": "./output/grpo_quick",
            "max_samples": 100,
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "reward_type": "accuracy",
            "logging_steps": 10,
            "save_steps": 100,
        }
    if name == "full":
        return {
            **common,
            "output_dir": "./output/grpo_full",
            "max_samples": None,
            "max_new_tokens": 512,
            "temperature": 0.8,
            "top_p": 0.9,
            "reward_type": "combined",
            "reward_config": {
                "components": [
                    {"type": "accuracy", "weight": 1.0},
                    {
                        "type": "length_penalty",
                        "weight": 0.5,
                        "target_length": 200,
                    },
                    {
                        "type": "step",
                        "weight": 0.3,
                        "step_bonus": 0.1,
                    },
                ]
            },
            "logging_steps": 100,
            "save_steps": 500,
        }
    raise ValueError("profile must be 'quick' or 'full'")


def validate_profile(parameters: Dict[str, Any]) -> TrainingConfig:
    """Validate public GRPO parameters without loading a model or dataset."""
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
        logging_steps=int(parameters["logging_steps"]),
        save_steps=int(parameters["save_steps"]),
        max_completion_length=int(parameters["max_new_tokens"]),
        num_generations=int(parameters["num_generations"]),
        temperature=float(parameters["temperature"]),
        top_p=float(parameters["top_p"]),
        kl_coef=float(parameters["kl_coef"]),
        clip_range=float(parameters["clip_range"]),
        use_lora=bool(parameters["use_lora"]),
        lora_r=int(parameters["lora_rank"]),
        lora_alpha=int(parameters["lora_alpha"]),
        lora_dropout=float(parameters["lora_dropout"]),
        lora_target_modules=list(parameters["lora_target_modules"]),
    )


def print_preview(profile: str, parameters: Dict[str, Any]) -> None:
    config = validate_profile(parameters)
    group = compute_group_advantages([1.0, 1.0, 0.0, 0.8])
    sample_count = parameters["max_samples"]

    print("=== GRPO 配置预览 ===")
    print(f"profile: {profile}")
    print(f"initial_policy: {config.model_name}")
    print(f"samples: {'all' if sample_count is None else sample_count}")
    print(f"epochs: {config.num_train_epochs:g}")
    print(
        "effective_batch_size (single process): "
        f"{config.effective_batch_size}"
    )
    print(f"num_generations: {config.num_generations}")
    print(
        f"generation: max_new_tokens={config.max_completion_length}, "
        f"temperature={config.temperature}, top_p={config.top_p}"
    )
    print(f"policy: kl_coef={config.kl_coef}, clip_range={config.clip_range}")
    print(f"reward_type: {parameters['reward_type']}")
    print("example_group_rewards: [1.0, 1.0, 0.0, 0.8]")
    print(f"example_group_mean: {group['mean_reward']:.1f}")
    rounded = [round(value, 1) for value in group["advantages"]]
    print(f"example_centered_advantages: {rounded}")
    print(f"output_dir: {config.output_dir}")


def run_training(
    parameters: Dict[str, Any],
    evaluate_samples: Optional[int],
) -> None:
    tool = RLTrainingTool()
    result = json.loads(tool.run(parameters))
    print("\n=== GRPO 训练结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") != "success":
        raise SystemExit(result.get("message", "GRPO training failed"))

    if evaluate_samples is None:
        return
    evaluation = json.loads(
        tool.run(
            {
                "action": "evaluate",
                "model_path": result["model_path"],
                "max_samples": evaluate_samples,
            }
        )
    )
    print("\n=== GSM8K 测试集评估 ===")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
    if evaluation.get("status") != "success":
        raise SystemExit(evaluation.get("message", "evaluation failed"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter 11.4 GRPO practice")
    parser.add_argument("--profile", choices=("quick", "full"), default="quick")
    parser.add_argument("--model-name")
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--run",
        action="store_true",
        help="load the SFT policy and GSM8K, then execute GRPO",
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
