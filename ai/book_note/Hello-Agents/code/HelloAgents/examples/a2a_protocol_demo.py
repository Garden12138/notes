"""Deterministic A2A collaboration practice for chapter 10.3."""

from __future__ import annotations

import json
from typing import Any

from hello_agents import A2AClient, A2AServer, SimpleAgent
from hello_agents.tools import A2ATool, ToolRegistry


def create_calculator() -> A2AServer:
    calculator = A2AServer(
        name="calculator-agent",
        description="专业的数学计算智能体",
        capabilities={"math": ["addition", "multiplication"]},
    )

    @calculator.skill("add", examples=["计算 10 + 5"])
    def add_numbers(query: str) -> str:
        """计算由加号分隔的一组数字。"""
        expression = query.replace("计算", "").replace("加上", "+")
        numbers = [float(value.strip()) for value in expression.split("+")]
        return f"计算结果: {' + '.join(map(str, numbers))} = {sum(numbers)}"

    @calculator.skill("multiply", examples=["计算 6 * 7"])
    def multiply_numbers(query: str) -> str:
        """计算由乘号分隔的一组数字。"""
        expression = query.replace("计算", "").replace("×", "*")
        numbers = [float(value.strip()) for value in expression.split("*")]
        result = 1.0
        for number in numbers:
            result *= number
        return f"计算结果: {' × '.join(map(str, numbers))} = {result}"

    @calculator.skill("info")
    def get_info(_: str) -> str:
        """返回 Agent 的名称和技能。"""
        return f"我是 {calculator.name}，支持 {', '.join(calculator.skills)}。"

    return calculator


def run_calculator() -> None:
    calculator = create_calculator()
    client = A2AClient.from_server(calculator)
    card = client.get_agent_card()

    print("=== Agent Card 与技能调用 ===")
    print("Agent:", card["name"])
    print("Skills:", ", ".join(skill["id"] for skill in card["skills"]))
    for skill, query in (
        ("info", "获取信息"),
        ("add", "计算 10 + 5"),
        ("multiply", "计算 6 * 7"),
    ):
        response = client.execute_skill(skill, query)
        print(f"{skill}: {response['result']} [{response['status']}]")


def create_content(topic: str) -> str:
    """Pass structured output through researcher, writer and editor Agents."""
    researcher = A2AServer("researcher", "负责搜索和分析资料")
    writer = A2AServer("writer", "根据研究资料撰写文章")
    editor = A2AServer("editor", "审校并批准文章")

    @researcher.skill("research")
    def research(text: str) -> dict[str, Any]:
        return {
            "topic": text,
            "findings": ["辅助影像分析", "支持个性化诊疗"],
            "sources": ["医学期刊", "临床指南"],
        }

    @writer.skill("write")
    def write(text: str) -> str:
        data = json.loads(text)
        findings = "、".join(data["findings"])
        return f"# {data['topic']}\n\n主要应用包括：{findings}。"

    @editor.skill("edit")
    def edit(text: str) -> dict[str, Any]:
        return {
            "article": text + "\n\n使用时仍需人工复核。",
            "feedback": "补充了使用边界",
            "approved": True,
        }

    research_result = A2AClient.from_server(researcher).execute_skill(
        "research",
        topic,
    )["result"]
    article = A2AClient.from_server(writer).execute_skill(
        "write",
        research_result,
    )["result"]
    return A2AClient.from_server(editor).execute_skill("edit", article)[
        "result"
    ]


class ReceptionistLLM:
    """Route one customer question and then consume the specialist result."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        self.calls = 0

    def invoke(self, messages: list[dict[str, str]], **_: Any) -> str:
        self.calls += 1
        if self.calls == 1:
            query = messages[-1]["content"]
            arguments = json.dumps(
                {"skill_name": "answer", "input": query},
                ensure_ascii=False,
            )
            return f"[TOOL_CALL:{self.tool_name}:{arguments}]"
        tool_result = messages[-1]["content"]
        tool_result = tool_result.split("工具执行结果：\n", 1)[-1]
        tool_result = tool_result.split("\n\n请基于", 1)[0]
        tool_result = tool_result.split("执行结果：\n", 1)[-1]
        return f"客服回复：{tool_result.strip()}"


def run_customer_service() -> None:
    tech = A2AServer("tech-expert", "回答技术问题")
    sales = A2AServer("sales-advisor", "回答销售问题")

    @tech.skill("answer")
    def answer_tech(question: str) -> str:
        return f"技术专家：{question} 可通过 REST API 和 Python SDK 接入。"

    @sales.skill("answer")
    def answer_sales(question: str) -> str:
        return f"销售顾问：{question} 请根据席位数申请企业报价。"

    cases = [
        ("tech_expert", tech, "你们的 API 如何调用？"),
        ("sales_advisor", sales, "企业版的价格是多少？"),
    ]
    print("\n=== A2ATool 与接待员 Agent ===")
    for tool_name, server, question in cases:
        registry = ToolRegistry()
        registry.register_tool(
            A2ATool(
                name=tool_name,
                description=server.description,
                client=A2AClient.from_server(server),
            ),
        )
        agent = SimpleAgent(
            name="receptionist",
            llm=ReceptionistLLM(tool_name),  # type: ignore[arg-type]
            system_prompt="识别问题类型，并转交给对应专家。",
            tool_registry=registry,
        )
        print(agent.run(question))


def run_negotiation() -> None:
    """Implement the chapter's proposal/counter-proposal as application data."""
    reviewer = A2AServer("reviewer", "评估任务周期并给出反提案")

    @reviewer.skill("propose")
    def propose(text: str) -> dict[str, Any]:
        proposal = json.loads(text)
        if int(proposal["deadline"]) >= 7:
            return {"accepted": True, "message": "接受提案"}
        return {
            "accepted": False,
            "message": "时间太紧",
            "counter_proposal": {"deadline": 7},
        }

    client = A2AClient.from_server(reviewer)
    proposal = {"task": "撰写技术报告", "deadline": 3}
    first = json.loads(
        client.execute_skill(
            "propose",
            json.dumps(proposal, ensure_ascii=False),
        )["result"],
    )
    print("\n=== Agent 间协商 ===")
    print("第 1 轮:", first)
    proposal.update(first["counter_proposal"])
    second = json.loads(
        client.execute_skill(
            "propose",
            json.dumps(proposal, ensure_ascii=False),
        )["result"],
    )
    print("第 2 轮:", second)


def main() -> None:
    run_calculator()
    print("\n=== 三 Agent 内容协作 ===")
    result = json.loads(create_content("AI 在医疗领域的应用"))
    print(result["article"])
    print("反馈:", result["feedback"])
    print("通过:", result["approved"])
    run_customer_service()
    run_negotiation()


if __name__ == "__main__":
    main()
