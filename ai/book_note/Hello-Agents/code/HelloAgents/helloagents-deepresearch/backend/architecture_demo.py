"""Offline verification of the section 14.1 architecture contract."""

from src.architecture import build_architecture_snapshot


def main() -> None:
    snapshot = build_architecture_snapshot()
    assert snapshot.scope == "chapter_14_1_architecture"
    assert len(snapshot.layers) == 4
    assert len(snapshot.agents) == 3
    assert len(snapshot.tools) == 2
    assert len(snapshot.data_flow) == 8
    assert [step.order for step in snapshot.data_flow] == list(range(1, 9))

    print("=== 14.1 深度研究助手架构实践 ===")
    print(f"layers: {len(snapshot.layers)}")
    print(f"agents: {len(snapshot.agents)}")
    print(f"tools: {len(snapshot.tools)}")
    print(f"data_flow_steps: {len(snapshot.data_flow)}")
    print(f"stream_endpoint: {snapshot.endpoint}")
    print("architecture_contract: ready")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()

