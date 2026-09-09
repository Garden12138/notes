"""Quick-start entry for the four RLTrainingTool operations in chapter 11.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from hello_agents import RLTrainingTool
from hello_agents.rl import create_accuracy_reward, evaluate_rewards


def run_tool(tool: RLTrainingTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
    result = json.loads(tool.run(parameters))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") != "success":
        raise RuntimeError(result.get("message", "RL operation failed"))
    return result


def reward_smoke_test() -> None:
    completions = [
        "8 + 5 = 13\nFinal Answer: 13",
        "8 + 5 = 12\nFinal Answer: 12",
        "I do not know",
    ]
    truths = ["13", "13", "13"]
    result = evaluate_rewards(completions, truths, create_accuracy_reward())
    print(json.dumps(result, ensure_ascii=False, indent=2))


def sft(tool: RLTrainingTool) -> Dict[str, Any]:
    return run_tool(
        tool,
        {
            "action": "train",
            "algorithm": "sft",
            "model_name": "Qwen/Qwen3-0.6B",
            "output_dir": "./output/quick_test/sft",
            "max_samples": 10,
            "num_epochs": 1,
            "batch_size": 2,
            "gradient_accumulation_steps": 4,
            "warmup_steps": 0,
            "use_lora": True,
            "lora_r": 8,
            "lora_alpha": 16,
        },
    )


def grpo(tool: RLTrainingTool) -> Dict[str, Any]:
    return run_tool(
        tool,
        {
            "action": "train",
            "algorithm": "grpo",
            "model_name": "Qwen/Qwen3-0.6B",
            "output_dir": "./output/quick_test/grpo",
            "max_samples": 5,
            "num_epochs": 1,
            "batch_size": 2,
            "gradient_accumulation_steps": 4,
            "num_generations": 8,
            "learning_rate": 1e-6,
            "warmup_steps": 0,
            "use_lora": True,
            "lora_r": 8,
            "lora_alpha": 16,
        },
    )


def evaluate(tool: RLTrainingTool, model_path: str) -> Dict[str, Any]:
    return run_tool(
        tool,
        {
            "action": "evaluate",
            "model_path": model_path,
            "max_samples": 10,
        },
    )


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Agentic-RL quick start")
    command.add_argument(
        "--stage",
        choices=("reward", "dataset", "sft", "grpo", "evaluate", "all"),
        default="reward",
        help="reward is a local smoke test; all follows the article's pipeline",
    )
    command.add_argument("--model-path", help="model or adapter path for evaluate")
    return command


def main() -> None:
    args = parser().parse_args()
    if args.stage == "reward":
        reward_smoke_test()
        return

    tool = RLTrainingTool()
    if args.stage == "dataset":
        run_tool(
            tool,
            {
                "action": "load_dataset",
                "format": "sft",
                "split": "train",
                "max_samples": 5,
            },
        )
    elif args.stage == "sft":
        sft(tool)
    elif args.stage == "grpo":
        grpo(tool)
    elif args.stage == "evaluate":
        if not args.model_path:
            raise SystemExit("--model-path is required for evaluate")
        evaluate(tool, args.model_path)
    else:
        sft(tool)
        grpo_result = grpo(tool)
        evaluate(tool, str(Path(grpo_result["output_dir"])))


if __name__ == "__main__":
    main()
