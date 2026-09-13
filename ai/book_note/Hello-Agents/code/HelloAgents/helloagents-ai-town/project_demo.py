"""Static verification of the Godot 15.5-15.6 scene and HTTP contracts."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "helloagents-ai-town"
RESOURCE_PATTERN = re.compile(r'path="(res://[^"]+)"')
AUTOLOAD_PATTERN = re.compile(r'^\w+="\*(res://[^"]+)"$', re.MULTILINE)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


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

    project = read("project.godot")
    main_scene = read("scenes/main.tscn")
    player_scene = read("scenes/player.tscn")
    npc_scene = read("scenes/npc.tscn")
    dialogue_scene = read("scenes/dialogue_ui.tscn")
    player = read("scripts/player.gd")
    npc = read("scripts/npc.gd")
    main_script = read("scripts/main.gd")
    dialogue_ui = read("scripts/dialogue_ui.gd")
    api_client = read("scripts/api_client.gd")
    config = read("scripts/config.gd")

    assert 'run/main_scene="res://scenes/main.tscn"' in project
    assert '[autoload]' in project
    assert 'Config="*res://scripts/config.gd"' in project
    assert 'APIClient="*res://scripts/api_client.gd"' in project

    resource_count = 0
    resource_sources = [ROOT / "project.godot", *sorted(ROOT.rglob("*.tscn"))]
    for source_path in resource_sources:
        content = source_path.read_text(encoding="utf-8")
        resources = RESOURCE_PATTERN.findall(content)
        if source_path.name == "project.godot":
            resources.extend(AUTOLOAD_PATTERN.findall(content))
        for resource in resources:
            resource_count += 1
            target = ROOT / resource.removeprefix("res://")
            assert target.is_file(), f"无效资源引用：{source_path.name} -> {resource}"

    assert '[node name="Player" type="CharacterBody2D"]' in player_scene
    assert all(
        f'[node name="{node}"' in player_scene
        for node in (
            "AnimatedSprite2D",
            "CollisionShape2D",
            "Camera2D",
            "InteractSound",
            "RunningSound",
        )
    )
    assert '[node name="NPC" type="CharacterBody2D"]' in npc_scene
    assert '[node name="InteractionArea" type="Area2D"' in npc_scene
    assert all(
        f'[node name="{node}"' in npc_scene
        for node in ("NameLabel", "DialogueLabel", "InteractionPrompt")
    )
    assert all(
        f'[node name="{node}"' in dialogue_scene
        for node in (
            "NPCName",
            "NPCTitle",
            "DialogueText",
            "PlayerInput",
            "SendButton",
            "CloseButton",
        )
    )
    assert "bbcode_enabled = true" in dialogue_scene
    assert '[node name="NPCs" type="Node2D"' in main_scene
    assert main_scene.count('instance=ExtResource("4_npc")') == 3
    assert '[node name="Background" type="Sprite2D"' in main_scene
    assert '[node name="Walls" type="StaticBody2D"' in main_scene
    assert '[node name="BackgroundMusic" type="AudioStreamPlayer"' in main_scene
    assert '[node name="APIClient"' not in main_scene

    assert all(key in player for key in ("KEY_W", "KEY_A", "KEY_S", "KEY_D"))
    assert all(key in player for key in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"))
    assert "KEY_E" in player and "interaction_requested.emit" in player
    assert "set_nearby_npc" in player and "set_interacting" in player
    assert "move_and_slide" in player and "_update_animation" in player

    assert all(
        key in npc
        for key in (
            "randf_range",
            "_choose_new_wander_target",
            "movement_bounds",
            "body_entered.connect",
            "body_exited.connect",
            "update_dialogue",
            "set_interacting",
        )
    )
    assert "player.set_nearby_npc(self)" in npc
    assert "player.set_nearby_npc(null)" in npc

    assert all(
        key in config
        for key in (
            "CYBER_TOWN_API_URL",
            "API_HEALTH",
            "API_CHAT",
            "API_NPC_STATUS",
            "API_NPCS",
            "NPC_STATUS_UPDATE_INTERVAL",
        )
    )
    assert all(
        signal in api_client
        for signal in (
            "chat_response_received",
            "chat_error",
            "npc_status_received",
            "npc_list_received",
        )
    )
    assert all(
        request in api_client
        for request in ("http_health", "http_chat", "http_status", "http_npcs")
    )
    assert api_client.count("HTTPRequest.new()") == 1
    assert all(
        endpoint in api_client
        for endpoint in (
            "Config.API_HEALTH",
            "Config.API_CHAT",
            "Config.API_NPC_STATUS",
            "Config.API_NPCS",
        )
    )
    assert "get_http_client_status" in api_client
    assert all(key in api_client for key in ("npc_name", "player_id", "message"))
    assert "response_npc != requested_npc" in api_client

    assert "append_text" in dialogue_ui and "add_text" in dialogue_ui
    assert "request_pending" in dialogue_ui
    assert "send_button.disabled" in dialogue_ui
    assert "npc_name != current_npc_name" in dialogue_ui

    assert "player.interaction_requested.connect" in main_script
    assert "player.set_interacting(true)" in main_script
    assert "current_npc.set_interacting(true)" in main_script
    assert "Config.NPC_STATUS_UPDATE_INTERVAL" in main_script
    assert "api_client.get_npc_status()" in main_script
    assert "npc.update_dialogue" in main_script
    assert "api_client.get_npc_list()" in main_script

    print("=== 15.6 Godot 前后端通信契约静态验证 ===")
    print(f"required_files: {len(required_files)}")
    print(f"resource_references: {resource_count}")
    print("autoload_config_and_api_client: ready")
    print("independent_http_channels: health_chat_status_npcs")
    print("chat_validation_and_correlation: ready")
    print("dialogue_history_and_pending_guard: ready")
    print("periodic_npc_status_bubbles: ready")
    print("npc_list_contract: ready")
    print("godot_runtime: not_executed")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
