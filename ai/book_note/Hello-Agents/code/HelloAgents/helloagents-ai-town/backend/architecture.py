"""Architecture contract implemented through section 15.3."""

from __future__ import annotations

from agents import NPC_ROLES
from models import (
    ArchitectureLayer,
    ArchitectureSnapshot,
    DataFlowStep,
    NPCProfile,
    SystemComponent,
)


NPC_CATALOG = [
    NPCProfile(
        id=role.npc_id,
        name=role.name,
        role=role.title,
        location=role.location,
        activity=role.activity,
        personality=role.personality,
    )
    for role in NPC_ROLES.values()
]


LAYERS = [
    ArchitectureLayer(
        name="game_frontend",
        technology="Godot 4.5 + GDScript",
        responsibilities=["2D 场景渲染", "玩家移动", "NPC 展示", "对话界面"],
        boundary=(
            "只处理表现和输入，不保存模型密钥，也不决定权威关系状态"
        ),
    ),
    ArchitectureLayer(
        name="backend",
        technology="FastAPI + Python 3.10+",
        responsibilities=["API 路由", "NPC 定位", "对话协调", "关系持久化"],
        boundary="校验游戏请求并协调 Agent，不承担画面渲染",
    ),
    ArchitectureLayer(
        name="agents",
        technology="HelloAgents",
        responsibilities=["角色扮演", "记忆", "好感度分析", "批量背景对话"],
        boundary="生成开放式内容，不直接修改 Godot 场景节点",
    ),
    ArchitectureLayer(
        name="external_services",
        technology="LLM API + SQLite（Qdrant 可替换）",
        responsibilities=["模型推理", "记忆检索", "结构化持久化"],
        boundary="提供基础能力，不决定 NPC 的交互流程",
    ),
]


COMPONENTS = [
    SystemComponent(
        name="Godot Scene Baseline",
        layer="game_frontend",
        status="implemented",
        responsibility="承载玩家、三个 NPC、交互提示和对话面板",
    ),
    SystemComponent(
        name="API Client",
        layer="game_frontend",
        status="implemented",
        responsibility="检查后端健康状态并异步提交对话请求",
    ),
    SystemComponent(
        name="NPC SimpleAgent Manager",
        layer="agents",
        status="implemented",
        responsibility="为每个 NPC 建立独立 Agent、Prompt、锁和会话入口",
    ),
    SystemComponent(
        name="Working and Episodic Memory",
        layer="agents",
        status="implemented",
        responsibility="按 NPC 与玩家隔离近期消息并检索相关历史互动",
    ),
    SystemComponent(
        name="Batch Background Dialogue Generator",
        layer="agents",
        status="implemented",
        responsibility="通过一次 LLM 调用生成三名 NPC 的背景内容并校验 JSON",
    ),
    SystemComponent(
        name="NPC-Player Affinity Manager",
        layer="backend",
        status="implemented",
        responsibility="分析互动、限制分值、映射等级并持久化玩家与 NPC 的关系",
    ),
    SystemComponent(
        name="Autonomous State and Logs",
        layer="backend",
        status="deferred",
        responsibility="更新 NPC 自主状态并记录结构化运行日志",
    ),
]


DATA_FLOW = [
    DataFlowStep(
        order=1,
        actor="Player",
        action="靠近 NPC 并按 E",
        status="implemented",
    ),
    DataFlowStep(
        order=2,
        actor="Godot",
        action="打开对话界面并提交消息",
        status="implemented",
    ),
    DataFlowStep(
        order=3,
        actor="FastAPI",
        action="校验请求并定位 NPC",
        status="implemented",
    ),
    DataFlowStep(
        order=4,
        actor="RelationshipManager",
        action="读取该 NPC 与玩家的当前好感度和对话修饰词",
        status="implemented",
    ),
    DataFlowStep(
        order=5,
        actor="Memory",
        action="检索近期与相关历史互动",
        status="implemented",
    ),
    DataFlowStep(
        order=6,
        actor="SimpleAgent",
        action="结合角色、关系、记忆和当前消息生成回复",
        status="implemented",
    ),
    DataFlowStep(
        order=7,
        actor="AffinityAnalyzer",
        action="分析玩家态度并返回结构化分值变化",
        status="implemented",
    ),
    DataFlowStep(
        order=8,
        actor="RelationshipManager",
        action="将好感度限制在 0～100 并写入 SQLite",
        status="implemented",
    ),
    DataFlowStep(
        order=9,
        actor="Backend",
        action="保存带关系元数据的对话记忆并返回结果",
        status="implemented",
    ),
    DataFlowStep(
        order=10,
        actor="Godot",
        action="展示 NPC 回复并恢复输入",
        status="implemented",
    ),
]


def build_architecture_snapshot() -> ArchitectureSnapshot:
    return ArchitectureSnapshot(
        project="helloagents-ai-town",
        scope="chapter_15_1_to_15_3_affinity_system",
        layers=LAYERS,
        components=COMPONENTS,
        data_flow=DATA_FLOW,
        implemented_capabilities=[
            "三个独立 SimpleAgent 及角色 Prompt",
            "容量 10、TTL 120 分钟的工作记忆",
            "基于 SQLite 与 TF-IDF 检索的情景记忆",
            "玩家消息的即时个性化回复",
            "一次调用生成三名 NPC 背景内容的批量生成器",
            "五档好感度、结构化 LLM 分析与动态对话风格",
            "NPC-玩家关系隔离、0～100 限幅和 SQLite 持久化",
            "FastAPI 对话响应与 Godot 异步展示链路",
        ],
        deferred_capabilities=[
            "NPC 自主状态更新与批量生成定时任务",
            "实时结构化日志",
            "Qdrant 生产向量存储适配",
        ],
    )
