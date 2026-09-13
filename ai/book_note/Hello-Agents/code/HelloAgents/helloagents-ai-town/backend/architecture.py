"""Architecture contract implemented through section 15.6."""

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
        responsibilities=["API 路由", "并发状态", "对话协调", "日志记录"],
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
        name="Godot Scene System",
        layer="game_frontend",
        status="implemented",
        responsibility=(
            "组合四个场景，处理移动、巡逻、碰撞、对话面板和定时背景气泡"
        ),
    ),
    SystemComponent(
        name="API Client",
        layer="game_frontend",
        status="implemented",
        responsibility="以独立异步通道处理健康、对话、NPC 状态和 NPC 列表请求",
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
        name="NPC State Manager",
        layer="backend",
        status="implemented",
        responsibility="原子管理忙碌状态，并定时生成和缓存三名 NPC 的背景对白",
    ),
    SystemComponent(
        name="Dialogue Logger",
        layer="backend",
        status="implemented",
        responsibility="将对话、记忆数量和关系变化同时写入控制台与每日文件",
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
        actor="NPCStateManager",
        action="原子占用 NPC；已忙碌则返回 409",
        status="implemented",
    ),
    DataFlowStep(
        order=5,
        actor="RelationshipManager",
        action="读取该 NPC 与玩家的当前好感度和对话修饰词",
        status="implemented",
    ),
    DataFlowStep(
        order=6,
        actor="Memory",
        action="检索近期与相关历史互动",
        status="implemented",
    ),
    DataFlowStep(
        order=7,
        actor="SimpleAgent",
        action="结合角色、关系、记忆和当前消息生成回复",
        status="implemented",
    ),
    DataFlowStep(
        order=8,
        actor="AffinityAnalyzer",
        action="分析玩家态度并返回结构化分值变化",
        status="implemented",
    ),
    DataFlowStep(
        order=9,
        actor="RelationshipManager",
        action="将好感度限制在 0～100 并写入 SQLite",
        status="implemented",
    ),
    DataFlowStep(
        order=10,
        actor="Memory",
        action="保存带关系元数据的对话记忆",
        status="implemented",
    ),
    DataFlowStep(
        order=11,
        actor="DialogueLogger",
        action="向控制台和当日日志文件记录完整结果",
        status="implemented",
    ),
    DataFlowStep(
        order=12,
        actor="NPCStateManager",
        action="无论成功或失败都在 finally 中释放 NPC",
        status="implemented",
    ),
    DataFlowStep(
        order=13,
        actor="Godot",
        action="展示 NPC 回复并恢复输入",
        status="implemented",
    ),
    DataFlowStep(
        order=14,
        actor="Godot Main",
        action="启动时并每 30 秒异步获取 NPC 背景对白",
        status="implemented",
    ),
    DataFlowStep(
        order=15,
        actor="Godot NPC",
        action="按 NPC 名称更新头顶背景气泡",
        status="implemented",
    ),
]


def build_architecture_snapshot() -> ArchitectureSnapshot:
    return ArchitectureSnapshot(
        project="helloagents-ai-town",
        scope="chapter_15_1_to_15_6_frontend_backend_communication",
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
            "NPC 忙碌状态的原子占用、409 冲突和 finally 释放",
            "每 30 秒批量更新一次背景对白，并提供缓存查询和手动刷新",
            "控制台与按日期文件双通道对话日志",
            "NPC 状态、单个/全部好感度查询接口",
            "FastAPI 对话响应与 Godot 异步展示链路",
            "Godot 四场景、玩家移动、NPC 巡逻、交互锁和回复气泡",
            "AutoLoad 配置和 API 客户端、独立 HTTP 通道与定时背景气泡",
        ],
        deferred_capabilities=[
            "Qdrant 生产向量存储适配",
            "Godot 好感度面板",
        ],
    )
