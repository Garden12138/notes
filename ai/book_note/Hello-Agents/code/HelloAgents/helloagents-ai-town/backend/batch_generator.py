"""One-call background dialogue generation for all Cyber Town NPCs."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from agents import NPC_ROLES, NPCRole


class BatchDialogueError(ValueError):
    """Raised when the model response violates the batch JSON contract."""


class NPCBatchGenerator:
    """Generate ambient dialogue for every NPC with one LLM request."""

    def __init__(
        self,
        llm: Any,
        npc_configs: dict[str, NPCRole] | None = None,
    ) -> None:
        self.llm = llm
        self.npc_configs = npc_configs or NPC_ROLES

    def generate_batch_dialogues(
        self,
        context: str | None = None,
    ) -> dict[str, str]:
        prompt = self._build_batch_prompt(context)
        response = self.llm.invoke(
            [
                {
                    "role": "system",
                    "content": (
                        "你是游戏 NPC 背景对话生成器，"
                        "负责创作自然、简短的办公室环境对白。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        return self._parse_dialogues(response)

    def _build_batch_prompt(self, context: str | None = None) -> str:
        scene = context.strip() if context and context.strip() else self._current_context()
        descriptions = "\n".join(
            (
                f"- {role.name}（{role.title}）：在{role.location}{role.activity}；"
                f"性格：{role.personality}"
            )
            for role in self.npc_configs.values()
        )
        output_example = {
            name: "..." for name in self.npc_configs
        }
        return f"""请为 Datawhale 办公室的 NPC 生成当前背景对话或行为描述。

场景：{scene}

NPC 信息：
{descriptions}

要求：
1. 每个 NPC 生成一句 20～40 字的内容。
2. 内容符合角色、当前活动和场景，可以是自言自语、工作状态或思考。
3. 只返回一个 JSON 对象，不要 Markdown 围栏或解释。
4. 必须包含且仅包含这些键：{list(self.npc_configs)}。

输出结构：
{json.dumps(output_example, ensure_ascii=False)}"""

    def _parse_dialogues(self, response: str) -> dict[str, str]:
        raw = response.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
        if fenced:
            raw = fenced.group(1).strip()
        if not raw.startswith("{"):
            start, end = raw.find("{"), raw.rfind("}")
            if start >= 0 and end > start:
                raw = raw[start : end + 1]

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise BatchDialogueError("批量对话不是合法 JSON") from error
        if not isinstance(parsed, dict):
            raise BatchDialogueError("批量对话必须是 JSON 对象")

        expected = set(self.npc_configs)
        actual = set(parsed)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise BatchDialogueError(
                f"NPC 键不匹配，缺少={missing}，多出={extra}",
            )
        dialogues: dict[str, str] = {}
        for name in self.npc_configs:
            value = parsed[name]
            if not isinstance(value, str) or not value.strip():
                raise BatchDialogueError(f"{name} 的背景对话必须是非空字符串")
            dialogues[name] = value.strip()
        return dialogues

    @staticmethod
    def _current_context(now: datetime | None = None) -> str:
        hour = (now or datetime.now()).hour
        if hour < 9:
            return "上班前，办公室刚刚亮灯"
        if hour < 12:
            return "上午工作时间"
        if hour < 14:
            return "午餐与短暂休息时间"
        if hour < 18:
            return "下午工作时间"
        return "临近下班，大家正在收尾"
