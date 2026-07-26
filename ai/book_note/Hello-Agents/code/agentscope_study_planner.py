"""Build and review a short learning plan with two AgentScope agents."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from agentscope.agent import ReActAgent
from agentscope.formatter import DeepSeekMultiAgentFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.pipeline import MsgHub
from dotenv import load_dotenv
from pydantic import BaseModel, Field


DEFAULT_MODEL_ID = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_GOAL = "掌握 LangGraph 基础，并完成一个带搜索节点的小项目"
DEFAULT_DAYS = 7
DEFAULT_HOURS_PER_DAY = 2.0
MAX_REVISIONS = 2
REQUIRED_SCORE = 10


class PlanReview(BaseModel):
    """Structured review returned by the reviewer agent."""

    approved: bool = Field(description="学习计划是否达到可执行标准")
    score: int = Field(ge=1, le=10, description="计划质量评分，1 到 10 分")
    strengths: list[str] = Field(
        default_factory=list,
        description="计划做得好的地方",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="仍需解决的问题",
    )
    revision_advice: list[str] = Field(
        default_factory=list,
        description="可直接执行的修改建议",
    )


def create_model() -> OpenAIChatModel:
    """Create an AgentScope model backed by the DeepSeek API."""
    load_dotenv()

    api_key = os.getenv("LLM_API_KEY", "").strip()
    model_id = os.getenv("LLM_MODEL_ID", "").strip() or DEFAULT_MODEL_ID
    base_url = os.getenv("LLM_BASE_URL", "").strip() or DEFAULT_BASE_URL

    if not api_key:
        raise RuntimeError("缺少环境变量 LLM_API_KEY。请先复制并填写 .env.example。")

    return OpenAIChatModel(
        model_name=model_id,
        api_key=api_key,
        stream=False,
        client_kwargs={"base_url": base_url},
        generate_kwargs={
            "temperature": 0.3,
            "max_tokens": 4096,
        },
    )


def create_agents(model: OpenAIChatModel) -> tuple[ReActAgent, ReActAgent]:
    """Create a planner and a reviewer with independent short-term memory."""
    planner = ReActAgent(
        name="学习规划师",
        sys_prompt=(
            "你是学习规划师。根据用户目标、天数和每日可用时间制定中文学习计划。"
            "计划必须按天列出学习目标、任务、预计时间和可验证产出。"
            "第一次发言提交初稿；收到审核意见后，只针对问题修订并提交完整新版。"
            "不要虚构外部资料链接。"
        ),
        model=model,
        formatter=DeepSeekMultiAgentFormatter(),
        memory=InMemoryMemory(),
        max_iters=3,
    )

    reviewer = ReActAgent(
        name="计划审核员",
        sys_prompt=(
            "你是严格但务实的学习计划审核员。审核最新计划是否覆盖用户目标，"
            "总时长是否超出预算，每天是否有明确产出，任务顺序是否合理。"
            "不要重写计划，只给出审核结论。只有评分为10分且没有阻塞问题时，"
            "approved 才能为 true。最终回复只能是一个合法 JSON 对象，不要使用 "
            "Markdown 代码块，也不要添加说明文字。JSON 必须包含 approved、score、"
            "strengths、issues、revision_advice 五个字段；后面三个字段的值必须是"
            "字符串数组。"
        ),
        model=model,
        formatter=DeepSeekMultiAgentFormatter(),
        memory=InMemoryMemory(),
        max_iters=3,
    )
    return planner, reviewer


def extract_first_json_object(text: str) -> dict[str, Any]:
    """Return the first JSON object found in model-generated text."""
    decoder = json.JSONDecoder()

    # Models occasionally wrap JSON in prose or a Markdown fence. Starting at
    # each opening brace keeps the parser tolerant without accepting non-JSON
    # field values.
    for position, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[position:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value

    raise RuntimeError(
        "审核员没有返回可解析的 JSON。请检查模型输出，或重新运行一次。",
    )


def parse_review(msg: Msg) -> PlanReview:
    """Extract and validate a JSON review without using model tool calls."""
    try:
        return PlanReview.model_validate(
            extract_first_json_object(msg.get_text_content().strip()),
        )
    except ValueError as error:
        raise RuntimeError(f"审核结果字段不合法：{error}") from error


def is_review_accepted(review: PlanReview) -> bool:
    """Apply the controller-owned acceptance rule."""
    return review.approved and review.score == REQUIRED_SCORE


def print_review(
    round_number: int,
    review: PlanReview,
    accepted: bool,
) -> None:
    """Print a compact review summary."""
    print(f"\n--- 第 {round_number} 次审核 ---")
    print(f"评分：{review.score}/10")
    print(f"审核员 approved：{review.approved}")
    print(
        "流程验收："
        + (
            "通过"
            if accepted
            else f"未通过（需 approved=true 且 score={REQUIRED_SCORE}）"
        ),
    )

    if review.strengths:
        print("优点：" + "；".join(review.strengths))
    if review.issues:
        print("问题：" + "；".join(review.issues))
    if review.revision_advice:
        print("修改建议：" + "；".join(review.revision_advice))


async def run_planning(
    goal: str,
    days: int,
    hours_per_day: float,
    max_revisions: int = MAX_REVISIONS,
) -> bool:
    """Run plan-review-revision collaboration and return acceptance status."""
    model = create_model()
    planner, reviewer = create_agents(model)

    task = Msg(
        name="用户",
        role="user",
        content=(
            f"请为目标“{goal}”制定学习计划。周期为 {days} 天，"
            f"每天最多 {hours_per_day:g} 小时。"
        ),
    )

    print("AgentScope 学习计划助手启动")
    print(task.get_text_content())

    accepted = False
    async with MsgHub(
        participants=[planner, reviewer],
        announcement=task,
    ) as hub:
        await planner()

        for review_round in range(1, max_revisions + 2):
            # DeepSeek thinking mode rejects the tool_choice request generated
            # by AgentScope's structured_model argument. Ask for JSON text and
            # validate it locally instead.
            review_msg = await reviewer()
            review = parse_review(review_msg)

            # The code, rather than the model's boolean alone, owns acceptance.
            accepted = is_review_accepted(review)
            print_review(review_round, review, accepted)
            if accepted:
                break

            if review_round > max_revisions:
                break

            await hub.broadcast(
                Msg(
                    name="流程控制器",
                    role="user",
                    content=(
                        f"第 {review_round} 次审核未通过。"
                        "请学习规划师根据审核员的最新意见提交完整修订版。"
                    ),
                ),
            )
            await planner()

    if accepted:
        print("\n✅ 学习计划已通过审核。")
    else:
        print(f"\n⚠️ 达到最多 {max_revisions} 次修订，学习计划仍未通过审核。")
    return accepted


def positive_int(value: str) -> int:
    """Parse a positive integer for argparse."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必须是正整数")
    return number


def positive_float(value: str) -> float:
    """Parse a positive float for argparse."""
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必须大于 0")
    return number


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="AgentScope 双 Agent 学习计划助手")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="学习目标")
    parser.add_argument("--days", type=positive_int, default=DEFAULT_DAYS, help="学习天数")
    parser.add_argument(
        "--hours-per-day",
        type=positive_float,
        default=DEFAULT_HOURS_PER_DAY,
        help="每天最多投入时间",
    )
    return parser.parse_args()


def main() -> None:
    """Run the command-line application."""
    args = parse_args()
    try:
        asyncio.run(
            run_planning(
                goal=args.goal,
                days=args.days,
                hours_per_day=args.hours_per_day,
            ),
        )
    except RuntimeError as error:
        print(f"运行失败：{error}")


if __name__ == "__main__":
    main()
