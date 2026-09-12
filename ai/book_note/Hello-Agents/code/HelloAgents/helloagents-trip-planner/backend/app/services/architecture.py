"""Serializable description of the section 13.1 system architecture."""

from __future__ import annotations

from typing import Mapping

from ..agents import build_agent_registry


LAYERS = (
    {
        "name": "frontend",
        "technology": "Vue 3 + TypeScript",
        "responsibilities": ["表单输入", "结果展示", "地图可视化"],
    },
    {
        "name": "backend",
        "technology": "FastAPI",
        "responsibilities": ["API 路由", "数据验证", "业务编排"],
    },
    {
        "name": "agents",
        "technology": "HelloAgents",
        "responsibilities": ["任务分解", "工具调用", "结果整合"],
    },
    {
        "name": "external_services",
        "technology": "MCP + HTTP API",
        "responsibilities": ["地图与天气", "图片", "LLM 推理"],
    },
)

DATA_FLOW = (
    "前端收集旅行需求",
    "后端校验请求",
    "景点搜索 Agent 获取候选景点",
    "天气查询 Agent 获取日期范围内的天气",
    "酒店推荐 Agent 获取住宿候选",
    "行程规划 Agent 整合结果并计算预算",
    "后端返回统一的旅行计划",
    "前端渲染行程、预算、地图和天气",
)


def build_architecture_snapshot(
    integration_status: Mapping[str, bool] | None = None,
) -> dict[str, object]:
    """Build a stable architecture payload for documentation and the UI."""
    status = dict(integration_status or {})
    return {
        "project": "helloagents-trip-planner",
        "scope": "chapter_13_1_to_13_6_features",
        "layers": list(LAYERS),
        "agents": [role.to_dict() for role in build_agent_registry()],
        "external_integrations": {
            "llm": {
                "purpose": "理解需求与生成行程",
                "configured": bool(status.get("llm")),
            },
            "amap": {
                "purpose": "景点、酒店、天气与路线数据",
                "configured": bool(status.get("amap")),
            },
            "unsplash": {
                "purpose": "目的地与景点图片",
                "configured": bool(status.get("unsplash")),
            },
        },
        "data_flow": list(DATA_FLOW),
        "implemented_capabilities": [
            "前后端连通",
            "配置状态检查",
            "四层架构与四个 Agent 的职责声明",
            "统一请求与响应数据模型",
            "FastAPI 请求校验入口",
            "四个 Agent 的固定顺序协作",
            "规划结果解析与业务规则校验",
            "行程规划 API 与依赖注入边界",
            "高德 MCP 工具发现与共享运行时装配",
            "Unsplash 景点图片补全",
            "旅行需求表单与请求状态",
            "行程、预算、天气与地图展示",
            "PNG 与 PDF 导出",
            "行程编辑、取消恢复与会话保存",
            "景点排序、删除与地图重建",
            "侧边导航与锚点跳转",
        ],
        "deferred_capabilities": [
            "通过 POI 搜索添加新景点",
        ],
    }
