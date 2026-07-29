"""Reflection Agent: execute, review, and refine an answer."""

from __future__ import annotations

from typing import Any

from ..core.agent import Agent
from ..core.config import Config
from ..core.llm import HelloAgentsLLM
from ..core.message import Message


DEFAULT_PROMPTS = {
    "initial": """请根据以下要求完成任务：
任务：{task}
请提供一个完整、准确的回答。""",
    "reflect": """请审查以下回答，并找出问题或改进空间：
原始任务：{task}
当前回答：{content}
请给出具体反馈；如果回答已经足够好，只回答“无需改进”。""",
    "refine": """请根据反馈改进回答：
原始任务：{task}
上一轮回答：{last_attempt}
反馈意见：{feedback}
请提供改进后的完整回答。""",
}


class Memory:
    """Store the short execution/reflection trajectory of one run."""

    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []

    def add_record(self, record_type: str, content: str) -> None:
        self.records.append({"type": record_type, "content": content})

    def get_trajectory(self) -> str:
        """Format all records for inspection."""
        labels = {
            "execution": "上一轮尝试",
            "reflection": "评审反馈",
        }
        return "\n\n".join(
            f"--- {labels.get(record['type'], record['type'])} ---\n"
            f"{record['content']}"
            for record in self.records
        )

    def get_last_execution(self) -> str:
        """Return the most recent generated answer."""
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return ""


class ReflectionAgent(Agent):
    """Improve an initial answer through bounded self-reflection."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
        max_iterations: int = 3,
        custom_prompts: dict[str, str] | None = None,
    ) -> None:
        super().__init__(name, llm, system_prompt, config)
        self.max_iterations = max_iterations
        self.memory = Memory()
        self.prompts = custom_prompts or DEFAULT_PROMPTS.copy()

    def run(self, input_text: str, **kwargs: Any) -> str:
        """Generate once, then alternate reflection and refinement."""
        self.memory = Memory()

        initial_prompt = self.prompts["initial"].format(task=input_text)
        initial_result = self._get_llm_response(
            initial_prompt,
            **kwargs,
        )
        self.memory.add_record("execution", initial_result)

        for _ in range(self.max_iterations):
            last_result = self.memory.get_last_execution()
            reflection_prompt = self.prompts["reflect"].format(
                task=input_text,
                content=last_result,
            )
            feedback = self._get_llm_response(
                reflection_prompt,
                **kwargs,
            )
            self.memory.add_record("reflection", feedback)

            if self._is_completion_feedback(feedback):
                break

            refine_prompt = self.prompts["refine"].format(
                task=input_text,
                last_attempt=last_result,
                feedback=feedback,
            )
            refined_result = self._get_llm_response(
                refine_prompt,
                **kwargs,
            )
            self.memory.add_record("execution", refined_result)

        final_result = self.memory.get_last_execution()
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(
            Message(content=final_result, role="assistant"),
        )
        return final_result

    @staticmethod
    def _is_completion_feedback(feedback: str) -> bool:
        """Stop only for a standalone, normalized completion signal."""
        normalized = feedback.strip().strip("。.!！?？\"'` ")
        return normalized.lower() in {
            "无需改进",
            "no need for improvement",
        }

    def _get_llm_response(self, prompt: str, **kwargs: Any) -> str:
        """Call the shared LLM interface."""
        return (
            self.llm.invoke(
                [{"role": "user", "content": prompt}],
                **kwargs,
            )
            or ""
        )
