"""Explicit real-model pipeline for chapter 12.4."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from hello_agents import (
    AIMEGenerator,
    HelloAgentsLLM,
    LLMJudgeTool,
    WinRateTool,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AIME-style problems and evaluate their quality."
    )
    parser.add_argument("--num-problems", type=int, default=10)
    parser.add_argument("--output-dir", default="./data_generation_results")
    parser.add_argument("--generation-reference-path")
    parser.add_argument("--evaluation-reference-path")
    parser.add_argument("--download-generation-reference", action="store_true")
    parser.add_argument("--download-evaluation-reference", action="store_true")
    parser.add_argument("--max-pairs", type=int, default=0)
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--judge-model")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.num_problems <= 0:
        raise SystemExit("--num-problems must be positive")
    if (
        not args.generation_reference_path
        and not args.download_generation_reference
    ):
        raise SystemExit(
            "Pass --generation-reference-path or explicitly allow "
            "--download-generation-reference."
        )
    if (
        not args.evaluation_reference_path
        and not args.download_evaluation_reference
    ):
        raise SystemExit(
            "Pass --evaluation-reference-path or explicitly allow "
            "--download-evaluation-reference."
        )
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_dir).expanduser().resolve() / timestamp
    generation_llm = HelloAgentsLLM(
        provider=args.provider,
        model=args.model,
        temperature=0.7,
    )
    judge_llm = HelloAgentsLLM(
        provider=args.provider,
        model=args.judge_model or args.model,
        temperature=0,
    )
    generation = AIMEGenerator(
        generation_llm,
        reference_data_path=args.generation_reference_path,
        download_reference=args.download_generation_reference,
        seed=args.seed,
    ).generate_and_save(
        args.num_problems,
        run_dir / "generated_data",
    )
    generated_path = generation["output_path"]
    absolute = json.loads(
        LLMJudgeTool(judge_llm).run(
            {
                "generated_data_path": generated_path,
                "output_dir": run_dir / "llm_judge",
            }
        )
    )
    paired = json.loads(
        WinRateTool(judge_llm).run(
            {
                "generated_data_path": generated_path,
                "reference_data_path": args.evaluation_reference_path,
                "download_reference": args.download_evaluation_reference,
                "output_dir": run_dir / "win_rate",
                "max_pairs": args.max_pairs,
                "seed": args.seed,
            }
        )
    )
    report = run_dir / "comprehensive_report.md"
    report.write_text(
        "\n".join(
            [
                "# 数据生成质量综合报告",
                "",
                f"- 生成成功：{generation['metadata']['generated']} / {args.num_problems}",
                f"- LLM Judge 平均分：{absolute.get('average_score', 'N/A')}",
                f"- LLM Judge 通过率：{absolute.get('pass_rate', 'N/A')}",
                f"- Win Rate：{paired.get('win_rate', 'N/A')}",
                "",
                "> 人工审核结果由 human_verification_ui.py 单独记录。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Run directory: {run_dir}")
    print(f"Generated: {generation['metadata']['generated']}")
    print(f"LLM Judge status: {absolute.get('status')}")
    print(f"Win Rate status: {paired.get('status')}")


if __name__ == "__main__":
    main()
