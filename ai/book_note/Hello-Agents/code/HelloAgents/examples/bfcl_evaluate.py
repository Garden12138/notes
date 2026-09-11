"""Run a real HelloAgents model on one local BFCL category."""

from __future__ import annotations

import argparse
import json

from hello_agents import BFCLEvaluationTool, HelloAgentsLLM, SimpleAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="bfcl_eval/data path")
    parser.add_argument("--category", default="simple_python")
    parser.add_argument("--max-samples", type=int, default=5)
    parser.add_argument("--output-dir", default="./evaluation_results")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--run-official-eval", action="store_true")
    parser.add_argument("--official-root", default=None)
    parser.add_argument("--official-model-name", default=None)
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
        name="BFCLTestAgent",
        llm=llm,
        system_prompt=(
            "你是函数调用助手。必须严格依据题目给出的函数定义输出调用，"
            "不要执行函数，也不要补充解释。"
        ),
        enable_tool_calling=False,
    )
    tool = BFCLEvaluationTool(args.data_dir)
    result = json.loads(
        tool.run(
            {
                "agent": agent,
                "category": args.category,
                "max_samples": args.max_samples,
                "output_dir": args.output_dir,
                "run_official_eval": args.run_official_eval,
                "official_root": args.official_root,
                "model_name": args.official_model_name or args.model,
            }
        )
    )
    if result.get("status") != "success":
        raise SystemExit(result.get("message", "BFCL evaluation failed"))
    print("BFCL evaluation completed")
    print(f"samples: {result['total_samples']}")
    print(f"local_ast_match_rate: {result['ast_match_rate']:.2%}")
    print(f"result_file: {result['bfcl_result_path']}")
    print(f"report_file: {result['report_path']}")
    print(
        "official_evaluation: "
        f"{result['official_evaluation']['status']}"
    )


if __name__ == "__main__":
    main()
