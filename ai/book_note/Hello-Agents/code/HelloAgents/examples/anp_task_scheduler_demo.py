"""Use ANPTool in SimpleAgent to route three compute tasks."""

from __future__ import annotations

import json
from typing import Any

from hello_agents import ANPDiscovery, SimpleAgent, register_service
from hello_agents.tools import ANPTool, ToolRegistry


COMPUTE_NODES = [
    ("compute_node_0", 0.55, 8, 32, False),
    ("compute_node_1", 0.42, 16, 64, True),
    ("compute_node_2", 0.18, 4, 16, False),
    ("compute_node_3", 0.65, 16, 64, True),
    ("compute_node_4", 0.23, 8, 32, True),
    ("compute_node_5", 0.12, 4, 16, False),
]


def build_compute_directory() -> ANPDiscovery:
    discovery = ANPDiscovery()
    for service_id, load, cpu, memory, gpu in COMPUTE_NODES:
        register_service(
            discovery=discovery,
            service_id=service_id,
            service_name=service_id.replace("compute_node_", "计算节点"),
            service_type="compute",
            capabilities=["data_processing", "ml_training"],
            endpoint=f"http://{service_id}:8000",
            metadata={
                "load": load,
                "cpu_cores": cpu,
                "memory_gb": memory,
                "gpu": gpu,
            },
        )
    return discovery


class DeterministicSchedulerLLM:
    """Choose a routing rule, then consume ANPTool's selected service."""

    def invoke(self, messages: list[dict[str, str]], **_: Any) -> str:
        latest = messages[-1]["content"]
        if "工具执行结果：" in latest:
            payload = latest.split("工具执行结果：\n", 1)[-1]
            payload = payload.split("\n\n请基于", 1)[0]
            payload = payload.split("执行结果：\n", 1)[-1]
            selected = json.loads(payload)
            metadata = selected["metadata"]
            return (
                f"选择 {selected['service_name']}"
                f"（{selected['service_id']}），负载 {metadata['load']:.2f}，"
                f"CPU {metadata['cpu_cores']} 核，内存 "
                f"{metadata['memory_gb']} GB，GPU={metadata['gpu']}。"
            )

        if "大型深度学习" in latest:
            arguments = {
                "action": "select_service",
                "service_type": "compute",
                "capabilities": "ml_training",
                "filters": {"gpu": True},
                "sort_by": "load",
                "ascending": True,
            }
        elif "高内存" in latest:
            arguments = {
                "action": "select_service",
                "service_type": "compute",
                "capabilities": "data_processing",
                "sort_by": "memory_gb",
                "ascending": False,
            }
        else:
            arguments = {
                "action": "select_service",
                "service_type": "compute",
                "capabilities": "data_processing",
                "sort_by": "load",
                "ascending": True,
            }
        encoded = json.dumps(arguments, ensure_ascii=False)
        return f"[TOOL_CALL:service_discovery:{encoded}]"


def main() -> None:
    registry = ToolRegistry()
    registry.register_tool(
        ANPTool(
            name="service_discovery",
            description=(
                "按能力、硬件配置和负载选择计算节点；"
                "使用 select_service，并传入 service_type、capabilities、"
                "filters、sort_by 和 ascending"
            ),
            discovery=build_compute_directory(),
        ),
    )
    scheduler = SimpleAgent(
        name="任务调度器",
        llm=DeterministicSchedulerLLM(),  # type: ignore[arg-type]
        system_prompt="根据任务需求，通过服务发现工具选择计算节点。",
        tool_registry=registry,
    )

    print("=== ANPTool 任务调度 ===")
    for task in (
        "训练一个大型深度学习模型，需要GPU支持",
        "处理大量文本数据，需要高内存",
        "运行轻量级数据分析任务",
    ):
        print("任务:", task)
        print("结果:", scheduler.run(task))


if __name__ == "__main__":
    main()
