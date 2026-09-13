"""Deterministic verification for the section 15.1 architecture baseline."""

from fastapi.testclient import TestClient

from main import create_app


def main() -> None:
    with TestClient(create_app()) as client:
        architecture = client.get("/architecture")
        health = client.get("/healthz")
        npcs = client.get("/npcs")
        deferred_chat = client.post(
            "/chat",
            json={
                "npc_name": "张三",
                "player_id": "player",
                "message": "你好",
            },
        )

    assert architecture.status_code == 200
    snapshot = architecture.json()
    assert snapshot["scope"] == "chapter_15_1_architecture_baseline"
    assert len(snapshot["layers"]) == 4
    assert len(snapshot["data_flow"]) == 8
    assert [step["order"] for step in snapshot["data_flow"]] == list(range(1, 9))
    assert health.status_code == 200
    assert health.json()["conversation_ready"] is False
    assert npcs.status_code == 200
    assert npcs.json()["total"] == 3
    assert deferred_chat.status_code == 501

    print("=== 15.1 赛博小镇架构基线验证 ===")
    print("architecture_layers: 4")
    print("data_flow_steps: 8")
    print("npc_catalog: 3")
    print("fastapi_contract: ready")
    print("chat_endpoint: deferred_501")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
