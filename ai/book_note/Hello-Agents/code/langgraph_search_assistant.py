"""基于 LangGraph 的三步问答助手：理解、搜索、回答。"""

import asyncio
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from tavily import TavilyClient


load_dotenv()


class SearchState(TypedDict):
    """三个节点共享的状态结构。"""

    messages: Annotated[list[AnyMessage], add_messages]
    user_query: str
    search_query: str
    search_results: str
    final_answer: str
    step: str


llm: ChatOpenAI | None = None
tavily_client: TavilyClient | None = None


def initialize_clients() -> None:
    """根据环境变量初始化 OpenAI 兼容模型与 Tavily 客户端。"""

    global llm, tavily_client

    model = (
        os.getenv("LLM_MODEL_ID", "").strip()
        or "deepseek-v4-flash"
    )
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = (
        os.getenv("LLM_BASE_URL", "").strip()
        or "https://api.deepseek.com"
    )
    tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()

    missing = [
        name
        for name, value in (
            ("LLM_MODEL_ID", model),
            ("LLM_API_KEY", api_key),
            ("LLM_BASE_URL", base_url),
            ("TAVILY_API_KEY", tavily_api_key),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"请在 .env 中配置：{', '.join(missing)}")

    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )
    tavily_client = TavilyClient(api_key=tavily_api_key)


def get_llm() -> ChatOpenAI:
    """返回已经初始化的模型客户端。"""

    if llm is None:
        raise RuntimeError("模型客户端尚未初始化，请先调用 initialize_clients()。")
    return llm


def get_tavily_client() -> TavilyClient:
    """返回已经初始化的 Tavily 客户端。"""

    if tavily_client is None:
        raise RuntimeError("Tavily 客户端尚未初始化，请先调用 initialize_clients()。")
    return tavily_client


def extract_search_query(response_text: str, fallback: str) -> str:
    """从模型的结构化文本中提取搜索词。"""

    for line in response_text.splitlines():
        stripped = line.strip()
        for prefix in ("搜索词：", "搜索关键词："):
            if stripped.startswith(prefix):
                query = stripped.removeprefix(prefix).strip()
                if query:
                    return query
    return fallback


def understand_query_node(state: SearchState) -> dict[str, object]:
    """步骤 1：理解用户查询并生成搜索关键词。"""

    user_message = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            user_message = str(message.content)
            break

    if not user_message:
        raise ValueError("状态中没有可处理的用户消息。")

    understand_prompt = f"""分析用户的查询："{user_message}"
请完成两个任务：
1. 简洁总结用户想要了解什么
2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

格式：
理解：[用户需求总结]
搜索词：[最佳搜索关键词]"""

    response = get_llm().invoke([SystemMessage(content=understand_prompt)])
    response_text = str(response.content)
    search_query = extract_search_query(response_text, user_message)

    return {
        "user_query": response_text,
        "search_query": search_query,
        "step": "understood",
        "messages": [AIMessage(content=f"我理解您的需求：{response_text}")],
    }


def tavily_search_node(state: SearchState) -> dict[str, object]:
    """步骤 2：使用 Tavily API 搜索实时信息。"""

    search_query = state["search_query"]

    try:
        print(f"🔍 正在搜索：{search_query}")
        response = get_tavily_client().search(
            query=search_query,
            search_depth="basic",
            include_answer=True,
            include_raw_content=False,
            max_results=5,
        )

        sections: list[str] = []
        if response.get("answer"):
            sections.append(f"综合答案：\n{response['answer']}")

        results = response.get("results") or []
        if results:
            items = []
            for index, result in enumerate(results[:3], start=1):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                items.append(
                    f"{index}. {title}\n{content}\n来源：{url}"
                )
            sections.append("相关信息：\n" + "\n\n".join(items))

        search_results = "\n\n".join(sections)
        if not search_results:
            search_results = "抱歉，没有找到相关信息。"

        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [
                AIMessage(content="✅ 搜索完成！正在为您整理答案……")
            ],
        }
    except Exception as error:
        error_message = f"搜索时发生错误：{error}"
        print(f"❌ {error_message}")
        return {
            "search_results": f"搜索失败：{error_message}",
            "step": "search_failed",
            "messages": [
                AIMessage(
                    content="❌ 搜索遇到问题，我将基于已有知识回答。"
                )
            ],
        }


def generate_answer_node(state: SearchState) -> dict[str, object]:
    """步骤 3：根据搜索状态生成最终答案。"""

    if state["step"] == "search_failed":
        answer_prompt = f"""搜索 API 暂时不可用，请基于已有知识回答用户的问题。

用户需求：
{state["user_query"]}

请提供有用的回答，并明确说明回答没有使用实时搜索结果。"""
    else:
        answer_prompt = f"""请根据以下搜索结果回答用户问题。

用户需求：
{state["user_query"]}

搜索结果：
{state["search_results"]}

要求：
1. 综合搜索结果，给出准确、有用的回答
2. 如果是技术问题，提供具体方案或代码
3. 引用重要信息的来源链接
4. 结构清晰；信息不完整时明确说明"""

    response = get_llm().invoke([SystemMessage(content=answer_prompt)])
    response_text = str(response.content)

    return {
        "final_answer": response_text,
        "step": "completed",
        "messages": [AIMessage(content=response_text)],
    }


def create_search_assistant():
    """构建并编译理解、搜索、回答的线性状态图。"""

    workflow = StateGraph(SearchState)
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    return workflow.compile(checkpointer=InMemorySaver())


def create_initial_state(user_input: str) -> SearchState:
    """为一次问答创建完整的初始状态。"""

    return {
        "messages": [HumanMessage(content=user_input)],
        "user_query": "",
        "search_query": "",
        "search_results": "",
        "final_answer": "",
        "step": "start",
    }


async def main() -> None:
    """运行可持续输入问题的命令行助手。"""

    try:
        initialize_clients()
    except ValueError as error:
        print(f"❌ 配置错误：{error}")
        return

    app = create_search_assistant()
    print("🔍 智能搜索助手启动！")
    print("我会使用 Tavily API 搜索最新信息。")
    print("输入 quit、q、exit 或 退出可结束程序。\n")

    session_count = 0
    while True:
        user_input = input("🤔 您想了解什么：").strip()
        if user_input.lower() in {"quit", "q", "exit", "退出"}:
            print("感谢使用，再见！")
            break
        if not user_input:
            continue

        session_count += 1
        config = {
            "configurable": {
                "thread_id": f"search-session-{session_count}"
            }
        }

        try:
            print("\n" + "=" * 60)
            async for output in app.astream(
                create_initial_state(user_input),
                config=config,
            ):
                for node_name, node_output in output.items():
                    messages = node_output.get("messages", [])
                    if not messages:
                        continue
                    latest_message = messages[-1]
                    if not isinstance(latest_message, AIMessage):
                        continue

                    if node_name == "understand":
                        print(f"🧠 理解阶段：{latest_message.content}")
                    elif node_name == "search":
                        print(f"🔍 搜索阶段：{latest_message.content}")
                    elif node_name == "answer":
                        print(f"\n💡 最终回答：\n{latest_message.content}")
            print("=" * 60 + "\n")
        except Exception as error:
            print(f"❌ 运行失败：{error}")
            print("请检查模型服务、网络和环境变量后重试。\n")


if __name__ == "__main__":
    asyncio.run(main())
