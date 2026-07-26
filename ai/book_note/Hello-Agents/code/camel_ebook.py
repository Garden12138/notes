"""Use CAMEL RolePlaying to create a popular-science psychology e-book."""

from __future__ import annotations

import os
from typing import Any

from camel.models import ModelFactory
from camel.societies import RolePlaying
from camel.types import ModelPlatformType
from dotenv import load_dotenv


TASK_DONE_MARKER = "<CAMEL_TASK_DONE>"
DEFAULT_TURN_LIMIT = 30
DEFAULT_MODEL_ID = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"

TASK_PROMPT = """
合作创作一本面向普通读者的中文科普电子书《拖延症心理学》，全文约 8000～10000 字。

内容要求：
1. 基于可靠的心理学理论和实证研究，解释拖延的形成机制、常见类型和影响因素；
2. 用通俗语言转译专业概念，配合贴近日常生活的案例；
3. 给出可执行的改善建议，避免把科普内容写成诊断或治疗意见；
4. 全书结构完整，至少包含引言、核心章节和总结，前后术语与观点保持一致；
5. 不得虚构研究、作者、论文或统计数据；无法确认的事实应明确标记为待核验。

协作分工：
- 心理学家是 AI User（指令发起者）：规划内容、提出每轮专业要求、检查事实和逻辑、
  审阅上一轮文本并给出修订意见。
- 心理学科普作家是 AI Assistant（指令执行者）：按照要求撰写或修改正文，负责叙事、
  语言表达和章节衔接，不把写作任务反向交给心理学家。

终止规则：
只有心理学家确认结构、专业性、可读性和完整性均达到要求后，才能在单独一行输出
<CAMEL_TASK_DONE>。心理学科普作家不得输出该标记。
""".strip()


def create_model() -> Any:
    """Create a CAMEL DeepSeek model backend."""
    load_dotenv()

    api_key = os.getenv("LLM_API_KEY", "").strip()
    model_id = os.getenv("LLM_MODEL_ID", "").strip() or DEFAULT_MODEL_ID
    base_url = os.getenv("LLM_BASE_URL", "").strip() or DEFAULT_BASE_URL

    if not api_key:
        raise RuntimeError("缺少环境变量 LLM_API_KEY。请先复制并填写 .env.example。")

    return ModelFactory.create(
        model_platform=ModelPlatformType.DEEPSEEK,
        model_type=model_id,
        url=base_url,
        api_key=api_key,
        model_config_dict={
            "temperature": 0.3,
            "max_tokens": 8192,
        },
    )


def create_session(model: Any) -> RolePlaying:
    """Create a role-playing session whose protocol roles match business duties."""
    return RolePlaying(
        user_role_name="心理学家",
        assistant_role_name="心理学科普作家",
        task_prompt=TASK_PROMPT,
        model=model,
        with_task_specify=False,
    )


def _termination_reason(response: Any) -> str:
    """Return a readable framework termination reason, if one exists."""
    if not getattr(response, "terminated", False):
        return ""

    info = getattr(response, "info", {}) or {}
    reasons = info.get("termination_reasons") or ["未提供原因"]
    if isinstance(reasons, (list, tuple, set)):
        return "；".join(str(reason) for reason in reasons)
    return str(reasons)


def _is_task_done(content: str) -> bool:
    """Accept the completion marker only when it appears on its own line."""
    return any(line.strip() == TASK_DONE_MARKER for line in content.splitlines())


def run_collaboration(
    session: RolePlaying,
    chat_turn_limit: int = DEFAULT_TURN_LIMIT,
) -> bool:
    """Run the conversation and return whether the psychologist accepted the book."""
    input_msg = session.init_chat()

    for turn in range(1, chat_turn_limit + 1):
        assistant_response, user_response = session.step(input_msg)

        assistant_reason = _termination_reason(assistant_response)
        user_reason = _termination_reason(user_response)
        if assistant_reason or user_reason:
            reasons = "；".join(reason for reason in (assistant_reason, user_reason) if reason)
            print(f"\n会话被框架终止：{reasons}")
            return False

        if assistant_response.msg is None or user_response.msg is None:
            print("\n会话未返回完整消息，协作提前结束。")
            return False

        print(f"\n{'=' * 24} 第 {turn} 轮 {'=' * 24}")
        print("\n心理学家（AI User / 指令发起者）：")
        print(user_response.msg.content)
        print("\n心理学科普作家（AI Assistant / 指令执行者）：")
        print(assistant_response.msg.content)

        # Only the subject-matter owner can accept the final manuscript.
        if _is_task_done(user_response.msg.content):
            print("\n心理学家已完成终审，电子书协作结束。")
            return True

        # RolePlaying.step() expects the assistant's previous message as next input.
        input_msg = assistant_response.msg

    print(f"\n达到最大轮数 {chat_turn_limit}，电子书尚未通过终审。")
    return False


def main() -> None:
    """Run the e-book collaboration from the command line."""
    try:
        model = create_model()
    except RuntimeError as error:
        print(f"配置错误：{error}")
        return

    print("CAMEL AI 科普电子书协作启动")
    print("心理学家负责专业要求与验收，心理学科普作家负责正文写作。")
    session = create_session(model)
    run_collaboration(session)


if __name__ == "__main__":
    main()
