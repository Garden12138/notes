"""Preview or execute the LoRA merge step described in section 11.6."""

from __future__ import annotations

import argparse
from pathlib import Path

from hello_agents.rl import merge_lora_adapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge a GRPO LoRA adapter")
    parser.add_argument(
        "--adapter-path",
        type=Path,
        default=Path("./output/agentic_rl/grpo_model"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output/agentic_rl/merged_model"),
    )
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    print("=== 11.6 LoRA 合并预览 ===")
    print(f"adapter_path: {args.adapter_path}")
    print(f"output_dir: {args.output_dir}")
    if not args.run:
        print("merge_started: False (add --run after GRPO finishes)")
        return

    destination = merge_lora_adapter(args.adapter_path, args.output_dir)
    print(f"merged_model_path: {destination}")


if __name__ == "__main__":
    main()
