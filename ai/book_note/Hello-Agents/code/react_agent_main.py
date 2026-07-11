"""
react_agent_main.py - ReAct Agent 测试入口

支持两种模式：
1. 本地 Mock 测试：不需要 LLM API / SerpApi Key，用来验证 ReAct 流程是否跑通。
   python react_agent_main.py --mock

2. 真实 LLM 测试：读取 .env 里的 LLM_* 配置，可选读取 SERPAPI_API_KEY。
   python react_agent_main.py "查询 Python 最新稳定版本，并说明来源"
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Callable

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 注意：这里保持和你现有文件名一致，是 too_executor.py，不是 tool_executor.py
from too_executor import ToolExecutor
from react_agent import ReActAgent


class MockLLM:
    """
    用于本地测试的假 LLM。
    它会模拟两轮 ReAct：第一轮调用 calculator，第二轮 Finish。
    """

    def __init__(self):
        self.call_count = 0

    def think(self, messages: list[dict[str, str]], temperature: float = 0) -> str:
        self.call_count += 1
        print("🧪 MockLLM 收到提示词，开始模拟响应...")

        if self.call_count == 1:
            return (
                "Thought: 我需要先计算 12 * 8 + 6 的结果。\n"
                "Action: calculator[12 * 8 + 6]"
            )

        return (
            "Thought: 我已经拿到了计算结果，可以给出最终答案。\n"
            "Action: Finish[12 * 8 + 6 = 102]"
        )


def safe_calculator(expression: str) -> str:
    """
    一个安全的四则运算工具，避免直接 eval 任意代码。
    支持：+、-、*、/、//、%、**、括号、正负号。
    """
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Load,
    )

    try:
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                return f"错误: 不支持的表达式节点 {type(node).__name__}"
            if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
                return "错误: 只支持数字常量。"

        result = eval(compile(tree, filename="<calculator>", mode="eval"), {"__builtins__": {}}, {})
        return str(result)
    except Exception as exc:
        return f"计算错误: {exc}"


def echo(text: str) -> str:
    """调试工具：原样返回输入。"""
    return text


def load_serpapi_search() -> Callable[[str], str] | None:
    """按需导入 SerpApi 搜索工具；缺少可选依赖时不影响 Mock 模式。"""
    try:
        from serpapi_tool import search
    except Exception as exc:
        print(f"⚠️ SerpApi 工具加载失败: {exc}")
        print("   如需使用搜索工具，请先安装依赖: pip install google-search-results")
        return None

    return search


def build_tool_executor(enable_search: bool = True) -> ToolExecutor:
    tool_executor = ToolExecutor()

    tool_executor.registerTool(
        name="calculator",
        description="用于执行安全的数学四则运算。输入示例: 12 * 8 + 6",
        func=safe_calculator,
    )

    tool_executor.registerTool(
        name="echo",
        description="调试工具，原样返回输入内容。",
        func=echo,
    )

    if enable_search:
        search_func = load_serpapi_search()
        if search_func:
            tool_executor.registerTool(
                name="search",
                description="基于 SerpApi 的网页搜索工具。输入应是搜索关键词。",
                func=search_func,
            )

    return tool_executor


def run_mock_demo(max_steps: int):
    tool_executor = build_tool_executor(enable_search=False)
    agent = ReActAgent(llm_client=MockLLM(), tool_executor=tool_executor, max_steps=max_steps)

    question = "请计算 12 * 8 + 6 等于多少？"
    answer = agent.run(question)
    print("\n=== Mock 测试完成 ===")
    print(answer)


def run_real_demo(question: str, max_steps: int):
    from llm import HelloAgentsLLM

    tool_executor = build_tool_executor(enable_search=True)
    llm_client = HelloAgentsLLM()
    agent = ReActAgent(llm_client=llm_client, tool_executor=tool_executor, max_steps=max_steps)

    answer = agent.run(question)
    print("\n=== ReAct 最终输出 ===")
    print(answer)


def main():
    parser = argparse.ArgumentParser(description="ReAct Agent 测试入口")
    parser.add_argument("question", nargs="*", help="要提问给 ReAct Agent 的问题")
    parser.add_argument("--mock", action="store_true", help="使用本地 MockLLM 测试，不调用真实模型")
    parser.add_argument("--max-steps", type=int, default=5, help="ReAct 最大推理/行动轮数")
    args = parser.parse_args()

    if args.mock:
        run_mock_demo(max_steps=args.max_steps)
        return

    question = " ".join(args.question).strip()
    if not question:
        question = "请搜索并总结一下 ReAct Agent 是什么。"

    run_real_demo(question=question, max_steps=args.max_steps)


if __name__ == "__main__":
    main()
