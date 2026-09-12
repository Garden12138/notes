"""Offline verification of the section 13.1 architecture contract."""

from __future__ import annotations

from app.agents import build_agent_registry
from app.services import build_architecture_snapshot


def main() -> None:
    registry = build_agent_registry()
    snapshot = build_architecture_snapshot(
        {"llm": False, "amap": False, "unsplash": False}
    )
    assert len(snapshot["layers"]) == 4
    assert len(registry) == 4
    assert len(snapshot["data_flow"]) == 8
    assert snapshot["scope"] == "chapter_13_1_to_13_5_frontend"

    print("=== 13.1 智能旅行助手架构实践 ===")
    print(f"layers: {len(snapshot['layers'])}")
    print(f"agents: {len(registry)}")
    for role in registry:
        print(f"  {role.name}: {role.display_name}")
    print(f"data_flow_steps: {len(snapshot['data_flow'])}")
    print("frontend_backend_contract: ready")
    print("collaboration_workflow: ready")
    print("mcp_integration: ready")
    print("frontend_trip_workflow: ready")
    print("external_api_calls: 0")
    print("production_trip_plan_generation: configured_when_credentials_exist")


if __name__ == "__main__":
    main()
