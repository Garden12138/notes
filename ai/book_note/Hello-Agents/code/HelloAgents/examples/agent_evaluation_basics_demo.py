"""Deterministic practice for the evaluation foundations in section 12.1."""

from __future__ import annotations

from collections import defaultdict

from hello_agents.evaluation import (
    EvaluationCase,
    EvaluationRunner,
    TokenUsage,
    token_f1,
)


class DemoAgent:
    """A fixed Agent-like object; it performs no model or network calls."""

    def __init__(self) -> None:
        self.attempts: dict[str, int] = defaultdict(int)
        self.last_usage: TokenUsage | None = None
        self.responses = {
            "中国的首都是哪里？": ("北京", TokenUsage(8, 4)),
            "6 × 7 等于多少？": ("42", TokenUsage(7, 2)),
            "查询今天的天气应该怎么做？": (
                "直接根据已有知识回答",
                TokenUsage(9, 5),
            ),
            "模拟一次可恢复请求": ("恢复完成", TokenUsage(10, 3)),
        }

    def run(self, prompt: str) -> str:
        self.attempts[prompt] += 1
        if prompt == "模拟一次可恢复请求" and self.attempts[prompt] == 1:
            raise TimeoutError("temporary timeout")
        response, usage = self.responses[prompt]
        self.last_usage = usage
        return response


def main() -> None:
    agent = DemoAgent()
    cases = [
        EvaluationCase("qa_001", "中国的首都是哪里？", "北京", "qa"),
        EvaluationCase("math_001", "6 × 7 等于多少？", ("42", "42.0"), "qa"),
        EvaluationCase(
            "tool_001",
            "查询今天的天气应该怎么做？",
            "调用搜索或天气工具",
            "tool_use",
        ),
        EvaluationCase(
            "robust_001",
            "模拟一次可恢复请求",
            "恢复完成",
            "robustness",
        ),
    ]
    runner = EvaluationRunner(
        predictor=agent.run,
        max_retries=1,
        usage_getter=lambda: agent.last_usage,
    )
    report = runner.evaluate(cases).to_dict(include_records=False)

    print("=== 12.1 智能体评估基础实践 ===")
    print(f"samples: {report['total_samples']}")
    print(f"accuracy: {report['accuracy']:.2%}")
    print(f"task_error_rate: {report['task_error_rate']:.2%}")
    print(
        "execution_failure_rate: "
        f"{report['execution_failure_rate']:.2%}"
    )
    print(f"failure_recovery_rate: {report['failure_recovery_rate']:.2%}")
    print(f"token_usage: {report['token_usage']}")
    print("category_accuracy:")
    for category, values in report["category_metrics"].items():
        print(f"  {category}: {values['accuracy']:.2%}")
    print(f"response_time_recorded: {report['average_response_time'] >= 0}")
    print(
        "token_f1_example: "
        f"{token_f1('use search tool', 'use the search tool'):.4f}"
    )


if __name__ == "__main__":
    main()
