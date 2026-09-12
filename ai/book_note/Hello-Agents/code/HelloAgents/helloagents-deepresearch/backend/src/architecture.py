"""Serializable description of the section 14.1–14.3 architecture."""

from __future__ import annotations

try:
    from .models import (
        AgentSpec,
        ArchitectureLayer,
        ArchitectureSnapshot,
        DataFlowStep,
        ToolSpec,
    )
except ImportError:  # Support ``python src/architecture.py`` style imports.
    from models import (  # type: ignore[no-redef]
        AgentSpec,
        ArchitectureLayer,
        ArchitectureSnapshot,
        DataFlowStep,
        ToolSpec,
    )


LAYERS = [
    ArchitectureLayer(
        name="frontend",
        technology="Vue 3 + TypeScript",
        responsibilities=["研究主题输入", "全屏研究面板", "Markdown 结果展示"],
    ),
    ArchitectureLayer(
        name="backend",
        technology="FastAPI",
        responsibilities=["请求校验", "研究流程编排", "SSE 事件推送"],
    ),
    ArchitectureLayer(
        name="agents",
        technology="HelloAgents",
        responsibilities=["TODO 规划", "任务总结", "报告生成"],
    ),
    ArchitectureLayer(
        name="external_services",
        technology="Search API + LLM API",
        responsibilities=["资料检索", "语言模型推理"],
    ),
]

AGENTS = [
    AgentSpec(
        name="TODO Planner",
        responsibility="把开放研究主题拆成 3–5 个可检索子任务",
        input="研究主题与当前日期",
        output="包含 title、intent、query 的 TODO 列表",
    ),
    AgentSpec(
        name="Task Summarizer",
        responsibility="从单个子任务的检索结果中提取事实和来源",
        input="TODO 与结构化搜索结果",
        output="带引用的 Markdown 任务总结",
    ),
    AgentSpec(
        name="Report Writer",
        responsibility="整合全部任务总结并消除重复",
        input="研究主题与已完成 TODO",
        output="带参考文献的 Markdown 报告",
    ),
]

TOOLS = [
    ToolSpec(name="SearchTool", responsibility="统一调用搜索引擎并返回来源"),
    ToolSpec(name="NoteTool", responsibility="保存阶段总结、来源和最终报告"),
]

DATA_FLOW = [
    DataFlowStep(order=1, name="user_input", description="用户输入研究主题"),
    DataFlowStep(order=2, name="sse_request", description="前端向 /research/stream 发起请求"),
    DataFlowStep(order=3, name="create_state", description="后端校验输入并创建研究状态"),
    DataFlowStep(order=4, name="planning", description="TODO Planner 生成研究子任务"),
    DataFlowStep(order=5, name="execution", description="逐项搜索、总结并写入笔记"),
    DataFlowStep(order=6, name="reporting", description="Report Writer 整合最终报告"),
    DataFlowStep(order=7, name="streaming", description="后端持续推送状态、任务和报告事件"),
    DataFlowStep(order=8, name="rendering", description="前端更新进度、日志和 Markdown 报告"),
]


def build_architecture_snapshot() -> ArchitectureSnapshot:
    """Build the architecture contract implemented through sections 14.1–14.3."""
    return ArchitectureSnapshot(
        project="helloagents-deepresearch",
        scope="chapter_14_1_to_14_3_agent_system",
        layers=LAYERS,
        agents=AGENTS,
        tools=TOOLS,
        endpoint="POST /research/stream",
        transport="Server-Sent Events over a streamed HTTP response",
        data_flow=DATA_FLOW,
        implemented_capabilities=[
            "四层架构与职责契约",
            "研究请求和 SSE 事件数据模型",
            "可注入的 TODO 研究协调器",
            "FastAPI 健康检查与架构接口",
            "POST 流式响应通道",
            "Vue 研究输入与全屏结果面板",
            "前端流式事件解析与取消请求",
            "Planner 草案校验与稳定任务编号",
            "规划、执行、报告三阶段状态流转",
            "搜索后端和结果上限向执行层传递",
            "逐任务搜索、总结、来源记录与状态事件",
            "失败任务标记和重复查询保护",
            "规划、总结和报告三个 Agent 服务",
            "角色 Prompt 与结构化交接",
            "ToolAwareSimpleAgent 调用监听",
            "工具调用事件向 SSE 协议桥接",
        ],
        deferred_capabilities=[
            "真实 HelloAgents LLM 初始化",
            "搜索引擎适配器",
            "NoteTool 持久化",
            "面向生产的规划、总结和报告服务",
        ],
    )
