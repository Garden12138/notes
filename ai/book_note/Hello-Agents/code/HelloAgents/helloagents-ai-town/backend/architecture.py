"""Architecture contract implemented for section 15.1."""

from __future__ import annotations

from models import (
    ArchitectureLayer,
    ArchitectureSnapshot,
    DataFlowStep,
    NPCProfile,
    SystemComponent,
)


NPC_CATALOG = [
    NPCProfile(
        id="zhang_san",
        name="张三",
        role="Python 工程师",
        location="开发区",
    ),
    NPCProfile(
        id="li_si",
        name="李四",
        role="产品经理",
        location="会议区",
    ),
    NPCProfile(
        id="wang_wu",
        name="王五",
        role="UI 设计师",
        location="设计区",
    ),
]


LAYERS = [
    ArchitectureLayer(
        name="game_frontend",
        technology="Godot 4.5 + GDScript",
        responsibilities=["2D 场景渲染", "玩家移动", "NPC 展示", "对话界面"],
        boundary="只处理表现和输入，不保存模型密钥，也不决定权威关系状态",
    ),
    ArchitectureLayer(
        name="backend",
        technology="FastAPI + Python 3.10+",
        responsibilities=["API 路由", "NPC 状态管理", "对话协调", "日志记录"],
        boundary="校验游戏请求并维护确定性状态，不承担画面渲染",
    ),
    ArchitectureLayer(
        name="agents",
        technology="HelloAgents",
        responsibilities=["NPC 角色扮演", "记忆管理", "好感度计算"],
        boundary="生成开放式内容，不直接修改 Godot 场景节点",
    ),
    ArchitectureLayer(
        name="external_services",
        technology="LLM API + Qdrant + SQLite",
        responsibilities=["模型推理", "向量检索", "结构化持久化"],
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
        responsibility="检查后端健康状态并预留对话 POST 请求",
    ),
    SystemComponent(
        name="Architecture API",
        layer="backend",
        status="implemented",
        responsibility="暴露健康检查、架构快照和 NPC 目录",
    ),
    SystemComponent(
        name="NPC SimpleAgent Manager",
        layer="agents",
        status="deferred",
        responsibility="为每个 NPC 建立独立 Agent、Prompt 和会话状态",
    ),
    SystemComponent(
        name="Memory and Affinity",
        layer="agents",
        status="deferred",
        responsibility="检索交互记忆并计算玩家关系变化",
    ),
    SystemComponent(
        name="Persistence and Logs",
        layer="external_services",
        status="deferred",
        responsibility="通过 Qdrant、SQLite 和日志文件保存运行数据",
    ),
]


DATA_FLOW = [
    DataFlowStep(order=1, actor="Player", action="靠近 NPC 并按 E", status="implemented"),
    DataFlowStep(order=2, actor="Godot", action="打开对话界面并提交消息", status="implemented"),
    DataFlowStep(order=3, actor="FastAPI", action="校验请求并定位 NPC", status="deferred"),
    DataFlowStep(order=4, actor="SimpleAgent", action="接收角色设定和玩家消息", status="deferred"),
    DataFlowStep(order=5, actor="Memory", action="检索相关历史互动", status="deferred"),
    DataFlowStep(order=6, actor="LLM", action="生成符合角色的回复", status="deferred"),
    DataFlowStep(order=7, actor="Backend", action="更新状态与好感度并记录日志", status="deferred"),
    DataFlowStep(order=8, actor="Godot", action="展示 NPC 回复并恢复输入", status="deferred"),
]


def build_architecture_snapshot() -> ArchitectureSnapshot:
    return ArchitectureSnapshot(
        project="helloagents-ai-town",
        scope="chapter_15_1_architecture_baseline",
        layers=LAYERS,
        components=COMPONENTS,
        data_flow=DATA_FLOW,
        implemented_capabilities=[
            "四层架构与职责边界",
            "FastAPI 健康检查、架构快照和 NPC 目录",
            "严格的对话请求数据模型",
            "Godot 主场景、玩家、NPC 和对话 UI 骨架",
            "WASD 移动、E 键交互与后端健康检查",
            "未实现对话返回 501，不生成伪造回复",
        ],
        deferred_capabilities=[
            "HelloAgents NPC 实例与角色 Prompt",
            "短期记忆和长期记忆",
            "好感度计算和关系状态",
            "NPC 自主状态更新与实时日志",
            "真实对话响应与数据持久化",
        ],
    )
