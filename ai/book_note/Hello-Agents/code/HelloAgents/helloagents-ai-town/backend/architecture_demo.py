"""Deterministic verification for the 15.1-15.2 Cyber Town practice."""

from __future__ import annotations

import json
from tempfile import TemporaryDirectory
from typing import Any

from fastapi.testclient import TestClient

from agents import NPCAgentManager
from batch_generator import NPCBatchGenerator
from config import Settings
from main import create_app


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
            return "解析器重构先固定输入契约，再用测试守住每个边界。"
        if "李四" in system_prompt:
            return "我这里还没有这个项目的记录，先说说它解决谁的问题？"
        return "我会先统一信息层级，再调整色彩和留白。"


def _empty_settings() -> Settings:
    return Settings(
        llm_model_id="",
        llm_api_key="",
        llm_base_url="",
    )


def main() -> None:
    fake_llm = FakeTownLLM()
    with TemporaryDirectory(prefix="cyber-town-memory-") as memory_root:
        manager = NPCAgentManager(fake_llm, memory_root=memory_root)

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
        zhang_prompt = fake_llm.calls[2][-1]["content"]
        li_prompt = fake_llm.calls[1][-1]["content"]
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
        assert snapshot["scope"] == "chapter_15_1_to_15_2_npc_agents"
        assert len(snapshot["layers"]) == 4
        assert len(snapshot["data_flow"]) == 8
        assert all(
            step["status"] == "implemented"
            for step in snapshot["data_flow"]
        )
        assert health.status_code == 200
        assert health.json()["conversation_ready"] is True
        assert npcs.status_code == 200 and npcs.json()["total"] == 3
        assert chat.status_code == 200
        assert chat.json()["npc_name"] == "张三"
        assert chat.json()["success"] is True
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

    print("=== 15.2 NPC 智能体系统离线验证 ===")
    print("npc_agents: 3_independent")
    print("role_prompts: 3_ready")
    print("memory_isolation: npc_and_player_ready")
    print("working_memory: capacity_10_ttl_120m")
    print("episodic_retrieval: ready")
    print("batch_background_dialogues: 3_in_1_call")
    print("chat_endpoint: ready")
    print("unknown_npc: 404")
    print("unconfigured_llm: 503")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
