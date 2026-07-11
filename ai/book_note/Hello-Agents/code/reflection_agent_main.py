#!/usr/bin/env python3
"""
reflection_agent_main.py - Reflection Agent 命令行执行入口。

真实模型模式:
    python reflection_agent_main.py "编写一个函数，返回不大于 n 的所有素数"

指定最大迭代次数:
    python reflection_agent_main.py \
        "编写一个函数，返回不大于 n 的所有素数" \
        --max-iterations 3

保存最终代码:
    python reflection_agent_main.py \
        "编写一个函数，返回不大于 n 的所有素数" \
        --output generated_solution.py

本地 Mock 测试:
    python reflection_agent_main.py --mock
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from reflection_agent import ReflectionAgent


INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
""".strip()


REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在<strong>算法效率</strong>上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
```python
{last_execution}
```

请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答“无需改进”。

请直接输出你的反馈，不要包含任何额外的解释。
""".strip()


REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
{last_execution}
评审员的反馈：
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
""".strip()


DEFAULT_TASK = "编写一个函数，返回所有不大于 n 的素数。"


class MockLLM:
    """用于验证 Reflection Agent 流程的本地模拟 LLM。"""

    def __init__(self) -> None:
        """初始化调用计数器。"""
        self.call_count = 0

    def think(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> str:
        """模拟初始代码、评审反馈、优化代码和终止反馈。"""
        del messages, temperature
        self.call_count += 1

        responses = {
            1: '''def find_primes(n: int) -> list[int]:
    """返回所有不大于 n 的素数。"""
    primes = []
    for candidate in range(2, n + 1):
        is_prime = True
        for divisor in range(2, candidate):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
    return primes''',
            2: (
                "当前算法最坏时间复杂度接近 O(n²)，因为每个候选数都可能"
                "试除到 candidate - 1。建议使用埃拉托斯特尼筛法，将时间复杂度"
                "降低到 O(n log log n)，并使用布尔数组批量标记合数。"
            ),
            3: '''def find_primes(n: int) -> list[int]:
    """使用埃拉托斯特尼筛法返回所有不大于 n 的素数。"""
    if n < 2:
        return []

    is_prime = bytearray(b"\\x01") * (n + 1)
    is_prime[0:2] = b"\\x00\\x00"

    limit = int(n ** 0.5)
    for number in range(2, limit + 1):
        if is_prime[number]:
            start = number * number
            is_prime[start:n + 1:number] = b"\\x00" * (
                ((n - start) // number) + 1
            )

    return [
        number
        for number in range(2, n + 1)
        if is_prime[number]
    ]''',
            4: "无需改进",
        }

        response = responses.get(self.call_count, "无需改进")
        print("🧪 MockLLM 响应:")
        print(response)
        return response


def build_parser() -> argparse.ArgumentParser:
    """创建并配置命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="运行 Reflection Agent，生成并迭代优化 Python 代码。",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="需要完成的 Python 编程任务。",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="最大反思与优化轮数，默认值为 3。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="将最终生成的代码保存到指定文件。",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="使用本地 MockLLM 测试，不调用真实模型。",
    )
    return parser


def create_llm_client(use_mock: bool):
    """创建 Mock 或真实 LLM 客户端。"""
    if use_mock:
        return MockLLM()

    try:
        from llm import HelloAgentsLLM
    except ImportError as exc:
        raise RuntimeError(
            "无法导入 llm.py 中的 HelloAgentsLLM。"
            "请确认 llm.py 位于当前目录，并已安装 openai 和 python-dotenv。"
        ) from exc

    return HelloAgentsLLM()


def save_code(code: str, output_path: Path) -> None:
    """将最终代码写入 UTF-8 文件。"""
    resolved_path = (
        output_path
        if output_path.is_absolute()
        else Path.cwd() / output_path
    )
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(code.rstrip() + "\n", encoding="utf-8")
    print(f"\n💾 最终代码已保存到: {resolved_path}")


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数并运行 Reflection Agent。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_iterations < 0:
        parser.error("--max-iterations 不能小于 0。")

    task = " ".join(args.task).strip()
    if not task:
        if args.mock:
            task = DEFAULT_TASK
        else:
            parser.error(
                "请提供编程任务，例如："
                'python reflection_agent_main.py "编写一个快速排序函数"'
            )

    try:
        llm_client = create_llm_client(use_mock=args.mock)
        code_agent = ReflectionAgent(
             llm_client=llm_client,
             initial_prompt_template=INITIAL_PROMPT_TEMPLATE,
             reflect_prompt_template=REFLECT_PROMPT_TEMPLATE,
             refine_prompt_template=REFINE_PROMPT_TEMPLATE,
             max_iterations=args.max_iterations,
        )
        final_code = code_agent.run(task)

        if args.output:
            save_code(final_code, args.output)

        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"\n❌ 执行失败: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断执行。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
