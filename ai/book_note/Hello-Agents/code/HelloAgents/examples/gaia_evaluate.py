"""Run a real HelloAgents model on an explicit local GAIA snapshot."""

from __future__ import annotations

import argparse
import json

from hello_agents import (
    GAIAEvaluationTool,
    GAIA_SYSTEM_PROMPT,
    HelloAgentsLLM,
    SimpleAgent,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="./data/gaia")
    parser.add_argument(
        "--split",
        choices=("validation", "test"),
        default="validation",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=(0, 1, 2, 3),
        default=1,
    )
    parser.add_argument("--max-samples", type=int, default=5)
    parser.add_argument("--output-dir", default="./evaluation_results")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--download", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_samples < 0:
        raise SystemExit("--max-samples cannot be negative")
    llm = HelloAgentsLLM(
        provider=args.provider,
        model=args.model,
        temperature=0.0,
    )
    agent = SimpleAgent(
        name="GAIATestAgent",
        llm=llm,
        system_prompt=GAIA_SYSTEM_PROMPT,
        enable_tool_calling=False,
    )
    result = json.loads(
        GAIAEvaluationTool(args.data_dir).run(
            {
                "agent": agent,
                "split": args.split,
                "level": args.level,
                "max_samples": args.max_samples,
                "output_dir": args.output_dir,
                "download": args.download,
            }
        )
    )
    if result.get("status") != "success":
        raise SystemExit(result.get("message", "GAIA evaluation failed"))
    score = result.get("exact_match_rate")
    score_text = f"{score:.2%}" if score is not None else "unscored"
    print("GAIA evaluation completed")
    print(f"samples: {result['total_samples']}")
    print(f"local_quasi_exact_match_rate: {score_text}")
    print(f"result_file: {result['gaia_result_path']}")
    print(f"report_file: {result['report_path']}")


if __name__ == "__main__":
    main()
