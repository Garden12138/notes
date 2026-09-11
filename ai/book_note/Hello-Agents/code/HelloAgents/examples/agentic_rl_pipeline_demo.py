"""Configuration preview and executable chapter 11.6 training pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hello_agents.rl import AgenticRLPipeline


DEFAULT_CONFIG = Path(__file__).with_name("agentic_rl_pipeline_config.json")


def print_preview(pipeline: AgenticRLPipeline) -> None:
    preview = pipeline.preview()
    print("=== 11.6 完整训练流水线预览 ===")
    print(f"base_model: {preview['base_model']}")
    print(f"train_samples: {preview['train_samples']}")
    print(f"evaluation_samples: {preview['evaluation_samples']}")
    print(f"sft_accuracy_threshold: {preview['sft_accuracy_threshold']:.2%}")
    print(
        "grpo_group_check: global_effective_batch="
        f"{preview['grpo_effective_batch']}, "
        f"world_size={preview['world_size']}, "
        f"num_generations={preview['num_generations']}"
    )
    for index, stage in enumerate(preview["stages"], start=1):
        print(f"stage_{index}: {stage}")
    print(f"results_path: {preview['results_path']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter 11.6 RL pipeline")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--run",
        action="store_true",
        help="download data and execute SFT, GRPO and evaluation",
    )
    args = parser.parse_args()

    pipeline = AgenticRLPipeline.from_file(args.config)
    if pipeline.is_main_process:
        print_preview(pipeline)
    if not args.run:
        if pipeline.is_main_process:
            print("pipeline_started: False (add --run after checking the config)")
        return

    result = pipeline.run()
    if pipeline.is_main_process:
        print("\n=== 流水线结果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
