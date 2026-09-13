"""Deterministic verification for sections 15.1 through 15.3."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi.testclient import TestClient

from agents import NPCAgentManager
from batch_generator import NPCBatchGenerator
from config import Settings
from main import create_app
from relationship_manager import RelationshipManager


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


def _empty_settings() -> Settings:
    return Settings(
        llm_model_id="",
        llm_api_key="",
        llm_base_url="",
    )


def _assert_affinity_levels() -> None:
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


def main() -> None:
    fake_llm = FakeTownLLM()
    _assert_affinity_levels()
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

    with TemporaryDirectory(prefix="cyber-town-") as workspace:
        relationship_path = Path(workspace) / "cyber_town.db"
        manager = NPCAgentManager(
            fake_llm,
            memory_root=Path(workspace) / "memory",
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
        episodic_hits = manager.memories["张三"].retrieve_memories(
            query="命令解析器",
            memory_types=["episodic"],
            limit=3,
            player_id="garden",
        )
        assert episodic_hits

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

        with TestClient(
            create_app(settings=_empty_settings(), npc_manager=manager),
        ) as client:
            architecture = client.get("/architecture")
            health = client.get("/healthz")
            npcs = client.get("/npcs")
            chat = client.post(
                "/chat",
                json={
                    "npc_name": "zhang_san",
                    "player_id": "garden",
                    "message": "代码评审先看什么？",
                },
            )
            unknown = client.post(
                "/chat",
                json={
                    "npc_name": "赵六",
                    "player_id": "garden",
                    "message": "你好",
                },
            )

        assert architecture.status_code == 200
        snapshot = architecture.json()
        assert snapshot["scope"] == "chapter_15_1_to_15_3_affinity_system"
        assert len(snapshot["layers"]) == 4
        assert len(snapshot["data_flow"]) == 10
        assert all(
            step["status"] == "implemented"
            for step in snapshot["data_flow"]
        )
        assert health.status_code == 200
        assert health.json()["conversation_ready"] is True
        assert npcs.status_code == 200 and npcs.json()["total"] == 3
        assert chat.status_code == 200
        assert chat.json()["npc_name"] == "张三"
        assert chat.json()["affinity_level"] == "熟悉"
        assert chat.json()["affinity_score"] == 24
        assert chat.json()["affinity_analysis_valid"] is True
        assert unknown.status_code == 404

        with TestClient(create_app(settings=_empty_settings())) as client:
            unavailable = client.post(
                "/chat",
                json={
                    "npc_name": "张三",
                    "player_id": "garden",
                    "message": "你好",
                },
            )
        assert unavailable.status_code == 503
        manager.close()

        reopened = RelationshipManager(fake_llm, relationship_path)
        assert reopened.get_affinity("张三", "garden").score == 24
        assert reopened.get_affinity("李四", "garden").score == 0
        assert reopened.get_affinity("王五", "visitor").score == 100
        reopened.close()

    print("=== 15.3 好感度系统离线验证 ===")
    print("affinity_levels: 5_boundaries_ready")
    print("initial_relationship: 0_stranger")
    print("dynamic_prompt: stranger_to_familiar_ready")
    print("structured_analysis: valid_and_invalid_ready")
    print("score_clamping: 0_to_100_ready")
    print("relationship_isolation: npc_and_player_ready")
    print("sqlite_persistence: restart_ready")
    print("chat_response: affinity_fields_ready")
    print("memory_and_batch_regression: ready")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
