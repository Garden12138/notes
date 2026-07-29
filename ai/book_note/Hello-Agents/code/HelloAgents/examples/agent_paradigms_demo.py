"""Offline checks for chapter 7 Agent flows and tool-call protocols."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from hello_agents import (
    FunctionCallAgent,
    PlanAndSolveAgent,
    ReActAgent,
    ReflectionAgent,
    SimpleAgent,
    ToolRegistry,
)


class SequenceLLM:
    """Return prepared responses without making network requests."""

    provider = "mock"

    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.prompts: list[str] = []

    def invoke(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        del kwargs
        self.prompts.append(messages[-1]["content"])
        return next(self.responses)


class FakeCompletions:
    """Mimic the SDK surface used by FunctionCallAgent."""

    def __init__(self, responses: list[Any]) -> None:
        self.responses = iter(responses)
        self.requests: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.requests.append(kwargs)
        return next(self.responses)


class FunctionCallLLM:
    """Expose a fake ``_client.chat.completions`` hierarchy."""

    provider = "mock"
    model = "mock-function-model"
    temperature = 0.0
    max_tokens = None

    def __init__(self, responses: list[Any]) -> None:
        self.completions = FakeCompletions(responses)
        self._client = SimpleNamespace(
            chat=SimpleNamespace(completions=self.completions),
        )


def make_response(
    content: str | None,
    tool_calls: list[Any] | None = None,
) -> Any:
    """Build the response shape returned by Chat Completions."""
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
    )


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_function(
        name="upper",
        description="将输入文字转成大写",
        func=str.upper,
    )
    return registry


def run_simple_agent() -> str:
    llm = SequenceLLM(
        ["先查询。[TOOL_CALL:upper:hello]", "工具结果是 HELLO。"],
    )
    agent = SimpleAgent(
        name="Simple",
        llm=llm,  # type: ignore[arg-type]
        tool_registry=build_registry(),
    )
    return agent.run("把 hello 转成大写")


def run_react_agent() -> str:
    llm = SequenceLLM(
        [
            "Thought: 需要转换文字。\nAction: upper[hello]",
            "Thought: 已取得结果。\nAction: Finish[HELLO]",
        ],
    )
    agent = ReActAgent(
        name="ReAct",
        llm=llm,  # type: ignore[arg-type]
        tool_registry=build_registry(),
    )
    return agent.run("把 hello 转成大写")


def run_function_call_agent() -> tuple[str, bool]:
    tool_call = SimpleNamespace(
        id="call_1",
        type="function",
        function=SimpleNamespace(
            name="upper",
            arguments='{"input": "hello"}',
        ),
    )
    llm = FunctionCallLLM(
        [
            make_response(None, [tool_call]),
            make_response("HELLO"),
        ],
    )
    agent = FunctionCallAgent(
        name="Function Call",
        llm=llm,  # type: ignore[arg-type]
        tool_registry=build_registry(),
    )
    result = agent.run("把 hello 转成大写")
    second_messages = llm.completions.requests[1]["messages"]
    tool_message_preserved = any(
        message.get("role") == "tool"
        and message.get("tool_call_id") == "call_1"
        and message.get("content") == "HELLO"
        for message in second_messages
    )
    return result, tool_message_preserved


def run_reflection_agent() -> tuple[str, int]:
    llm = SequenceLLM(
        [
            "第一版答案",
            "还需补充例子；目前不满足“无需改进”的条件。",
            "加入例子后的第二版答案",
            "无需改进。",
        ],
    )
    agent = ReflectionAgent(
        name="Reflection",
        llm=llm,  # type: ignore[arg-type]
        max_iterations=3,
    )
    return agent.run("写一个简短说明"), len(agent.memory.records)


def run_plan_and_solve_agent() -> tuple[str, bool]:
    llm = SequenceLLM(
        [
            '```python\n["收集信息", "形成结论"]\n```',
            "已收集关键信息",
            "最终结论",
        ],
    )
    agent = PlanAndSolveAgent(
        name="Plan-and-Solve",
        llm=llm,  # type: ignore[arg-type]
    )
    result = agent.run("完成两步任务")
    return result, "已收集关键信息" in llm.prompts[-1]


def main() -> None:
    print(f"SimpleAgent: {run_simple_agent()}")
    print(f"ReActAgent: {run_react_agent()}")

    function_result, tool_message_preserved = run_function_call_agent()
    print(
        "FunctionCallAgent: "
        f"{function_result}（原生 tool 消息已回传："
        f"{tool_message_preserved}）",
    )

    reflection_result, reflection_records = run_reflection_agent()
    print(
        "ReflectionAgent: "
        f"{reflection_result}（轨迹 {reflection_records} 条）",
    )

    plan_result, history_passed = run_plan_and_solve_agent()
    print(
        "PlanAndSolveAgent: "
        f"{plan_result}（上一步结果已传递：{history_passed}）",
    )


if __name__ == "__main__":
    main()
