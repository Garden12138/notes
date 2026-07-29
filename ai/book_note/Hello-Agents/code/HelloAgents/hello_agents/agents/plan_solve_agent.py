"""Plan-and-Solve Agent: create a static plan, then execute each step."""

from __future__ import annotations

import ast
from typing import Any

from ..core.agent import Agent
from ..core.config import Config
from ..core.llm import HelloAgentsLLM
from ..core.message import Message


DEFAULT_PLANNER_PROMPT = """你是一个 AI 规划专家。
请把问题分解为按顺序执行的独立步骤。

问题：{question}

只按以下格式输出 Python 字符串列表：
```python
["步骤1", "步骤2", "步骤3"]
```"""

DEFAULT_EXECUTOR_PROMPT = """你是一个 AI 执行专家。
请只完成当前步骤，并仅输出该步骤的结果。

原始问题：{question}
完整计划：{plan}
历史步骤与结果：
{history}
当前步骤：{current_step}
"""


class Planner:
    """Ask the LLM for a Python-list plan and parse it safely."""

    def __init__(
        self,
        llm_client: HelloAgentsLLM,
        prompt_template: str | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_template = prompt_template or DEFAULT_PLANNER_PROMPT

    def plan(self, question: str, **kwargs: Any) -> list[str]:
        """Return the fenced Python list produced by the model."""
        prompt = self.prompt_template.format(question=question)
        response = (
            self.llm_client.invoke(
                [{"role": "user", "content": prompt}],
                **kwargs,
            )
            or ""
        )
        try:
            plan_text = response.split("```python", 1)[1].split(
                "```",
                1,
            )[0].strip()
            parsed = ast.literal_eval(plan_text)
        except (IndexError, SyntaxError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return [str(step) for step in parsed]


class Executor:
    """Execute a static plan while passing earlier step results forward."""

    def __init__(
        self,
        llm_client: HelloAgentsLLM,
        prompt_template: str | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_template = prompt_template or DEFAULT_EXECUTOR_PROMPT

    def execute(
        self,
        question: str,
        plan: list[str],
        **kwargs: Any,
    ) -> str:
        """Return the result of the final plan step."""
        history = ""
        final_answer = ""
        for index, step in enumerate(plan, start=1):
            prompt = self.prompt_template.format(
                question=question,
                plan=plan,
                history=history or "无",
                current_step=step,
            )
            final_answer = (
                self.llm_client.invoke(
                    [{"role": "user", "content": prompt}],
                    **kwargs,
                )
                or ""
            )
            history += (
                f"步骤 {index}：{step}\n"
                f"结果：{final_answer}\n\n"
            )
        return final_answer


class PlanAndSolveAgent(Agent):
    """Compose the chapter's Planner and Executor."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
        custom_prompts: dict[str, str] | None = None,
    ) -> None:
        super().__init__(name, llm, system_prompt, config)
        custom_prompts = custom_prompts or {}
        self.planner = Planner(llm, custom_prompts.get("planner"))
        self.executor = Executor(llm, custom_prompts.get("executor"))

    def run(self, input_text: str, **kwargs: Any) -> str:
        """Plan the task once and execute the resulting steps in order."""
        plan = self.planner.plan(input_text, **kwargs)
        if plan:
            final_answer = self.executor.execute(
                input_text,
                plan,
                **kwargs,
            )
        else:
            final_answer = "无法生成有效的行动计划，任务终止。"

        self.add_message(Message(content=input_text, role="user"))
        self.add_message(
            Message(content=final_answer, role="assistant"),
        )
        return final_answer
