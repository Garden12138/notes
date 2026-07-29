"""ReAct Agent: alternate reasoning, tool action, and observation."""

from __future__ import annotations

import re
from typing import Any

from ..core.agent import Agent
from ..core.config import Config
from ..core.llm import HelloAgentsLLM
from ..core.message import Message
from ..tools.base import Tool
from ..tools.registry import ToolRegistry


DEFAULT_REACT_PROMPT = """你是一个具备推理和行动能力的 AI 助手。

## 可用工具
{tools}

## 输出协议
每次只执行一个步骤，并严格输出：
Thought: 分析当前信息与下一步。
Action: 工具名[参数]

信息足够时输出：
Thought: 得出结论。
Action: Finish[最终答案]

## 当前任务
Question: {question}

## 执行历史
{history}
"""


class ReActAgent(Agent):
    """Drive the classic Thought → Action → Observation loop."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry | None = None,
        system_prompt: str | None = None,
        config: Config | None = None,
        max_steps: int = 5,
        custom_prompt: str | None = None,
    ) -> None:
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry or ToolRegistry()
        self.max_steps = max_steps
        self.current_history: list[str] = []
        self.prompt_template = custom_prompt or DEFAULT_REACT_PROMPT

    def add_tool(self, tool: Tool) -> None:
        """Register one Tool for later actions."""
        self.tool_registry.register_tool(tool)

    def run(self, input_text: str, **kwargs: Any) -> str:
        """Run until ``Finish[...]`` or the step limit is reached."""
        self.current_history = []

        for _ in range(self.max_steps):
            prompt = self.prompt_template.format(
                tools=self.tool_registry.get_tools_description(),
                question=input_text,
                history="\n".join(self.current_history) or "无",
            )
            response = self.llm.invoke(
                [{"role": "user", "content": prompt}],
                **kwargs,
            )
            thought, action = self._parse_output(response)
            if not action:
                self.current_history.append(
                    "Observation: 无法解析 Action，请严格遵循输出协议。",
                )
                continue

            if action.startswith("Finish["):
                final_answer = self._parse_action_input(action)
                self._save_turn(input_text, final_answer)
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or tool_input is None:
                self.current_history.append(
                    "Observation: 无效的 Action 格式。",
                )
                continue

            observation = self.tool_registry.execute_tool(
                tool_name,
                tool_input,
            )
            if thought:
                self.current_history.append(f"Thought: {thought}")
            self.current_history.append(f"Action: {action}")
            self.current_history.append(f"Observation: {observation}")

        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        self._save_turn(input_text, final_answer)
        return final_answer

    def _save_turn(self, input_text: str, output_text: str) -> None:
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(
            Message(content=output_text, role="assistant"),
        )

    @staticmethod
    def _parse_output(text: str) -> tuple[str | None, str | None]:
        """Extract the Thought and Action lines."""
        thought_match = re.search(
            r"Thought:\s*(.*?)(?=\nAction:|$)",
            text,
            re.DOTALL,
        )
        action_match = re.search(r"Action:\s*(.+)", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    @staticmethod
    def _parse_action(
        action_text: str,
    ) -> tuple[str | None, str | None]:
        """Split ``tool_name[input]``."""
        match = re.fullmatch(r"([^\[\]]+)\[(.*)\]", action_text, re.DOTALL)
        if not match:
            return None, None
        return match.group(1).strip(), match.group(2).strip()

    @classmethod
    def _parse_action_input(cls, action_text: str) -> str:
        """Return the content enclosed by one action."""
        _, action_input = cls._parse_action(action_text)
        return action_input or ""
