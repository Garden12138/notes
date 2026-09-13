"""Static verification of the Godot-to-15.3-backend contract."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "helloagents-ai-town"
RESOURCE_PATTERN = re.compile(r'path="(res://[^"]+)"')


def main() -> None:
    required_files = [
        "project.godot",
        "scenes/main.tscn",
        "scenes/player.tscn",
        "scenes/npc.tscn",
        "scenes/dialogue_ui.tscn",
        "scripts/main.gd",
        "scripts/player.gd",
        "scripts/npc.gd",
        "scripts/dialogue_ui.gd",
        "scripts/api_client.gd",
        "scripts/config.gd",
    ]
    for relative_path in required_files:
        assert (ROOT / relative_path).is_file(), f"缺少 Godot 文件：{relative_path}"

    project = (ROOT / "project.godot").read_text(encoding="utf-8")
    assert 'run/main_scene="res://scenes/main.tscn"' in project

    resource_count = 0
    for source_path in [ROOT / "project.godot", *sorted(ROOT.rglob("*.tscn"))]:
        content = source_path.read_text(encoding="utf-8")
        for resource in RESOURCE_PATTERN.findall(content):
            resource_count += 1
            target = ROOT / resource.removeprefix("res://")
            assert target.is_file(), f"无效资源引用：{source_path.name} -> {resource}"

    player = (ROOT / "scripts/player.gd").read_text(encoding="utf-8")
    npc = (ROOT / "scripts/npc.gd").read_text(encoding="utf-8")
    api_client = (ROOT / "scripts/api_client.gd").read_text(encoding="utf-8")
    dialogue_ui = (ROOT / "scripts/dialogue_ui.gd").read_text(encoding="utf-8")
    assert all(key in player for key in ("KEY_W", "KEY_A", "KEY_S", "KEY_D"))
    assert "KEY_E" in npc and "interaction_requested" in npc
    assert "/healthz" in api_client and "/chat" in api_client
    assert all(key in api_client for key in ("npc_name", "player_id", "message"))
    assert "conversation_ready" in dialogue_ui

    print("=== 15.1～15.3 Godot 对话契约静态验证 ===")
    print(f"required_files: {len(required_files)}")
    print(f"resource_references: {resource_count}")
    print("main_scene_contract: ready")
    print("movement_and_interaction_contract: ready")
    print("chat_request_and_response_contract: ready")
    print("godot_runtime: not_executed")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
