"""Deterministic, offline practice for section 12.2."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from hello_agents import BFCLDataset, BFCLEvaluationTool
from hello_agents.evaluation import match_function_calls


class FixedBFCLAgent:
    """Return fixed responses so the evaluation pipeline is reproducible."""

    name = "FixedBFCLAgent"

    def run(self, prompt: str) -> str:
        if "triangle" in prompt:
            return "calculate_triangle_area(height=2+3, base=10)"
        if "Send an email" in prompt:
            return json.dumps(
                {
                    "name": "send_email",
                    "arguments": {"subject": "Hello", "recipient": "Ada"},
                }
            )
        if "Beijing and Shanghai" in prompt:
            return (
                "```python\n"
                "get_weather(city='Shanghai')\n"
                "get_weather(city='Beijing')\n"
                "```"
            )
        if "without using a tool" in prompt:
            return "[]"
        return 'get_weather(city="Shanghai")'


def main() -> None:
    data_dir = Path(__file__).parent / "data" / "bfcl"
    available_categories = BFCLDataset(
        data_dir,
        category="demo",
    ).get_available_categories()
    tool = BFCLEvaluationTool(data_dir)
    with tempfile.TemporaryDirectory(prefix="helloagents-bfcl-") as output_dir:
        result = json.loads(
            tool.run(
                {
                    "agent": FixedBFCLAgent(),
                    "category": "demo",
                    "max_samples": 0,
                    "output_dir": output_dir,
                    "run_official_eval": False,
                }
            )
        )
        assert result["status"] == "success", result
        assert result["total_samples"] == 5
        assert result["correct_samples"] == 4
        assert result["category_statistics"]["simple"]["accuracy"] == 0.5
        exported = Path(result["bfcl_result_path"])
        report = Path(result["report_path"])
        export_count = len(exported.read_text(encoding="utf-8").splitlines())

        arithmetic_match = match_function_calls(
            "calculate(x=2+3)",
            [{"calculate": {"x": [5]}}],
        )
        print("=== 12.2 BFCL 工具调用评估实践 ===")
        print(f"available_categories: {available_categories}")
        print(f"samples: {result['total_samples']}")
        print(f"accuracy: {result['overall_accuracy']:.2%}")
        print(f"ast_match_rate: {result['ast_match_rate']:.2%}")
        print(f"weighted_accuracy: {result['weighted_accuracy']:.2%}")
        print(f"function_name_accuracy: {result['function_name_accuracy']:.2%}")
        print(f"parameter_accuracy: {result['parameter_accuracy']:.2%}")
        print(f"call_f1: {result['f1_score']:.2%}")
        print("category_accuracy:")
        for category, stats in result["category_statistics"].items():
            print(f"  {category}: {stats['accuracy']:.2%}")
        print(f"constant_arithmetic_match: {arithmetic_match}")
        print(f"official_jsonl_records: {export_count}")
        print(f"report_generated: {report.is_file()}")
        print(f"official_evaluation: {result['official_evaluation']['status']}")


if __name__ == "__main__":
    main()
