"""Deterministic verification for sections 15.1 through 15.4."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi.testclient import TestClient

from agents import NPCAgentManager
from batch_generator import NPCBatchGenerator
from config import Settings
from logger import DialogueLogger
from main import create_app
from relationship_manager import RelationshipManager
from state_manager import NPCStateManager
from view_logs import read_tail


class FakeTownLLM:
    """Record prompts and return deterministic text without external calls."""

    provider = "fake"

    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []
        self.batch_calls = 0

    def invoke(
        self,
        messages: list[dict[str, str]],
        **_: Any,
    ) -> str:
        self.calls.append([dict(message) for message in messages])
        system_prompt = messages[0]["content"]
        current_input = messages[-1]["content"]
        if "判断一轮 NPC 对话是否应改变好感度" in system_prompt:
            if "格式测试" in current_input:
                return "not-json"
            if any(word in current_input for word in ("谢谢", "请教", "真棒")):
                return json.dumps(
                    {
                        "should_change": True,
                        "change_amount": 5,
                        "reason": "友好感谢",
                        "sentiment": "positive",
                    },
                    ensure_ascii=False,
                )
            if any(word in current_input for word in ("太差", "讨厌", "攻击")):
                return json.dumps(
                    {
                        "should_change": True,
                        "change_amount": -8,
                        "reason": "不友好批评",
                        "sentiment": "negative",
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {
                    "should_change": False,
                    "change_amount": 0,
                    "reason": "普通交流",
                    "sentiment": "neutral",
                },
                ensure_ascii=False,
            )
        if "背景对话生成器" in system_prompt:
            self.batch_calls += 1
            return json.dumps(
                {
                    "张三": "这个解析器边界条件还得再补两组测试。",
                    "李四": "先把用户路径画清楚，再决定需求优先级。",
                    "王五": "这组间距统一以后，界面呼吸感好多了。",
                },
                ensure_ascii=False,
            )
        if "触发失败" in current_input:
            raise RuntimeError("fake role failure")
        if "张三" in system_prompt:
            if "命令解析器" in current_input and "还记得" in current_input:
                return "记得，你在重构命令解析器；先补边界测试，再拆分解析步骤。"
            if "当前与玩家的关系：熟悉" in system_prompt:
                return "我们已经熟悉了，我可以把评审清单和重构步骤都发给你。"
            return "解析器重构先固定输入契约，再用测试守住每个边界。"
        if "李四" in system_prompt:
            return "我这里还没有这个项目的记录，先说说它解决谁的问题？"
        return "我会先统一信息层级，再调整色彩和留白。"

    def role_calls(self, npc_name: str) -> list[list[dict[str, str]]]:
        return [
            call
            for call in self.calls
            if npc_name in call[0]["content"]
            and "判断一轮 NPC 对话是否应改变好感度"
            not in call[0]["content"]
        ]


def _empty_settings(log_path: str | Path = "./logs") -> Settings:
    return Settings(
        llm_model_id="",
        llm_api_key="",
        llm_base_url="",
        log_path=str(log_path),
        npc_update_interval=3600,
    )


def _assert_affinity_protocol() -> None:
    expected = {
        0: "陌生",
        20: "陌生",
        21: "熟悉",
        40: "熟悉",
        41: "友好",
        60: "友好",
        61: "亲密",
        80: "亲密",
        81: "挚友",
        100: "挚友",
    }
    for score, level in expected.items():
        assert RelationshipManager.get_affinity_level(score) == level

    invalid = RelationshipManager.parse_analysis("not-json")
    assert invalid.valid is False and invalid.change_amount == 0
    invalid_reason = RelationshipManager.parse_analysis(
        json.dumps(
            {
                "should_change": True,
                "change_amount": 3,
                "reason": "这段原因明显超过了十个汉字",
                "sentiment": "positive",
            },
            ensure_ascii=False,
        ),
    )
    assert invalid_reason.valid is False
    inconsistent_no_change = RelationshipManager.parse_analysis(
        json.dumps(
            {
                "should_change": False,
                "change_amount": 2,
                "reason": "普通交流",
                "sentiment": "neutral",
            },
            ensure_ascii=False,
        ),
    )
    assert inconsistent_no_change.valid is False


def main() -> None:
    fake_llm = FakeTownLLM()
    _assert_affinity_protocol()

    with TemporaryDirectory(prefix="cyber-town-") as workspace:
        root = Path(workspace)
        relationship_path = root / "cyber_town.db"
        log_dir = root / "logs"
        manager = NPCAgentManager(
            fake_llm,
            memory_root=root / "memory",
            relationship_database_path=relationship_path,
        )

        first_reply = manager.chat(
            "张三",
            "我正在重构命令解析器。",
            player_id="garden",
        )
        li_reply = manager.chat(
            "李四",
            "你记得我的项目吗？",
            player_id="garden",
        )
        recalled_reply = manager.chat(
            "张三",
            "你还记得我的项目吗？",
            player_id="garden",
        )
        assert "输入契约" in first_reply
        assert "没有这个项目的记录" in li_reply
        assert "命令解析器" in recalled_reply
        zhang_prompt = fake_llm.role_calls("张三")[1][-1]["content"]
        li_prompt = fake_llm.role_calls("李四")[0][-1]["content"]
        assert "玩家说：我正在重构命令解析器。" in zhang_prompt
        assert "命令解析器" not in li_prompt
        assert manager.agents["张三"] is not manager.agents["李四"]
        assert manager.memories["张三"] is not manager.memories["李四"]
        assert manager.get_npc_memories("张三", player_id="visitor") == []

        zhang_stats = manager.memory_stats("张三")
        li_stats = manager.memory_stats("李四")
        assert zhang_stats["working"]["count"] == 4
        assert zhang_stats["episodic"]["count"] == 2
        assert li_stats["working"]["count"] == 2
        assert li_stats["episodic"]["count"] == 1
        assert zhang_stats["working"]["capacity"] == 10
        assert zhang_stats["working"]["ttl_minutes"] == 120

        manager.relationship_manager.set_affinity("张三", 19, "garden")
        positive = manager.chat_with_affinity(
            "张三",
            "谢谢你的建议！",
            player_id="garden",
        )
        assert positive.affinity.old_affinity == 19
        assert positive.affinity.new_affinity == 24
        assert positive.affinity.old_level == "陌生"
        assert positive.affinity.new_level == "熟悉"
        assert "当前与玩家的关系：陌生" in (
            fake_llm.role_calls("张三")[-1][0]["content"]
        )

        neutral = manager.chat_with_affinity(
            "张三",
            "今天天气不错。",
            player_id="garden",
        )
        assert neutral.affinity.changed is False
        assert neutral.affinity.new_affinity == 24
        assert "当前与玩家的关系：熟悉" in (
            fake_llm.role_calls("张三")[-1][0]["content"]
        )

        manager.relationship_manager.set_affinity("李四", 2, "garden")
        negative = manager.chat_with_affinity(
            "李四",
            "这个方案太差了。",
            player_id="garden",
        )
        assert negative.affinity.new_affinity == 0
        assert negative.affinity.change_amount == -2

        manager.relationship_manager.set_affinity("王五", 99, "visitor")
        upper_bound = manager.chat_with_affinity(
            "王五",
            "谢谢你的设计建议。",
            player_id="visitor",
        )
        assert upper_bound.affinity.new_affinity == 100
        assert upper_bound.affinity.change_amount == 1

        before_invalid = manager.get_affinity("王五", "garden")
        invalid_update = manager.chat_with_affinity(
            "王五",
            "格式测试",
            player_id="garden",
        )
        assert invalid_update.affinity.analysis_valid is False
        assert invalid_update.affinity.new_affinity == before_invalid.score

        generator = NPCBatchGenerator(fake_llm)
        dialogues = generator.generate_batch_dialogues("下午工作时间")
        assert set(dialogues) == {"张三", "李四", "王五"}
        assert fake_llm.batch_calls == 1

        logger = DialogueLogger(log_dir=log_dir, console=False)
        state = NPCStateManager(
            batch_generator=generator,
            update_interval=3600,
            error_reporter=logger.log_error,
            refresh_reporter=logger.log_state_refresh,
        )
        app = create_app(
            settings=_empty_settings(log_dir),
            npc_manager=manager,
            state_manager=state,
            dialogue_logger=logger,
        )
        with TestClient(app) as client:
            openapi = client.get("/openapi.json")
            architecture = client.get("/architecture")
            health = client.get("/healthz")
            npcs = client.get("/npcs")
            status_all = client.get("/npcs/status")
            status_one = client.get("/npcs/zhang_san/status")
            affinity = client.get(
                "/npcs/张三/affinity",
                params={"player_id": "garden"},
            )
            affinity_compatibility = client.get("/affinity/张三/garden")
            all_affinities = client.get(
                "/affinities",
                params={"player_id": "garden"},
            )

            assert state.try_begin_dialogue("张三", "other-player") is True
            conflict = client.post(
                "/chat",
                json={
                    "npc_name": "张三",
                    "player_id": "garden",
                    "message": "这次请求应该冲突。",
                },
            )
            assert state.is_npc_busy("张三") is True
            state.finish_dialogue("张三", "other-player")

            chat = client.post(
                "/chat",
                json={
                    "npc_name": "zhang_san",
                    "player_id": "garden",
                    "message": "代码评审先看什么？",
                },
            )
            state_after_chat = client.get("/npcs/张三/status")
            failed = client.post(
                "/chat",
                json={
                    "npc_name": "王五",
                    "player_id": "garden",
                    "message": "触发失败",
                },
            )
            state_after_failure = client.get("/npcs/王五/status")
            refreshed = client.post("/npcs/status/refresh")
            unknown = client.post(
                "/chat",
                json={
                    "npc_name": "赵六",
                    "player_id": "garden",
                    "message": "你好",
                },
            )

            assert openapi.status_code == 200
            assert {
                "/chat",
                "/npcs/status",
                "/npcs/status/refresh",
                "/npcs/{npc_name}/status",
                "/npcs/{npc_name}/affinity",
                "/affinity/{npc_name}/{player_id}",
                "/affinities",
            }.issubset(openapi.json()["paths"])
            assert architecture.status_code == 200
            snapshot = architecture.json()
            assert snapshot["scope"] == "chapter_15_1_to_15_5_godot_scene"
            assert len(snapshot["layers"]) == 4
            assert len(snapshot["data_flow"]) == 13
            assert all(
                step["status"] == "implemented"
                for step in snapshot["data_flow"]
            )
            assert health.status_code == 200
            assert health.json()["conversation_ready"] is True
            assert health.json()["state_scheduler_running"] is True
            assert npcs.status_code == 200 and npcs.json()["total"] == 3
            assert status_all.status_code == 200
            assert len(status_all.json()["npcs"]) == 3
            assert set(status_all.json()["dialogues"]) == {
                "张三",
                "李四",
                "王五",
            }
            assert status_all.json()["scheduler_running"] is True
            assert status_one.status_code == 200
            assert status_one.json()["npc_name"] == "张三"
            assert affinity.status_code == 200
            assert affinity.json()["score"] == 24
            assert affinity_compatibility.json() == affinity.json()
            assert set(all_affinities.json()["affinities"]) == {
                "张三",
                "李四",
                "王五",
            }
            assert conflict.status_code == 409
            assert chat.status_code == 200
            assert chat.json()["npc_name"] == "张三"
            assert chat.json()["affinity_level"] == "熟悉"
            assert chat.json()["affinity_score"] == 24
            assert chat.json()["affinity_analysis_valid"] is True
            assert state_after_chat.json()["is_busy"] is False
            assert state_after_chat.json()["last_interaction"] is not None
            assert failed.status_code == 502
            assert state_after_failure.json()["is_busy"] is False
            assert refreshed.status_code == 200
            assert set(refreshed.json()["dialogues"]) == {
                "张三",
                "李四",
                "王五",
            }
            assert unknown.status_code == 404
            assert fake_llm.batch_calls == 3

        assert state.running is False
        log_files = list(log_dir.glob("dialogue_*.log"))
        assert len(log_files) == 1
        log_text = log_files[0].read_text(encoding="utf-8")
        assert "NPC 背景对白已更新" in log_text
        assert "代码评审先看什么" in log_text
        assert "好感度" in log_text
        assert read_tail(log_files[0], 3)
        logger.close()

        with TestClient(
            create_app(
                settings=_empty_settings(root / "empty-logs"),
                start_background_tasks=True,
            ),
        ) as client:
            unavailable = client.post(
                "/chat",
                json={
                    "npc_name": "张三",
                    "player_id": "garden",
                    "message": "你好",
                },
            )
            refresh_unavailable = client.post("/npcs/status/refresh")
        assert unavailable.status_code == 503
        assert refresh_unavailable.status_code == 503

        manager.close()
        reopened = RelationshipManager(fake_llm, relationship_path)
        assert reopened.get_affinity("张三", "garden").score == 24
        assert reopened.get_affinity("李四", "garden").score == 0
        assert reopened.get_affinity("王五", "visitor").score == 100
        reopened.close()

    print("=== 15.4 后端服务离线验证 ===")
    print("npc_agents_memory_affinity: regression_ready")
    print("busy_state: atomic_409_and_finally_release_ready")
    print("background_scheduler: startup_and_manual_refresh_ready")
    print("state_api: list_single_and_cache_ready")
    print("affinity_api: single_compatibility_and_all_ready")
    print("daily_dialogue_log: console_file_contract_ready")
    print("lifespan: scheduler_start_stop_ready")
    print("sqlite_persistence: restart_ready")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
