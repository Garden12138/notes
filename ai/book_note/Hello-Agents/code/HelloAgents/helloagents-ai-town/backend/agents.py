"""Independent HelloAgents NPCs with role prompts and conversation memory."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Callable


# The chapter keeps the game beside the learning framework instead of packaging
# the framework as a dependency. Add that shared source root for direct runs.
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
if str(FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK_ROOT))

from hello_agents import HelloAgentsLLM, SimpleAgent  # noqa: E402
from hello_agents.memory import MemoryConfig, MemoryItem, MemoryManager  # noqa: E402

from relationship_manager import (  # noqa: E402
    AffinitySnapshot,
    AffinityUpdate,
    RelationshipManager,
)


@dataclass(frozen=True)
class NPCRole:
    """Stable role information shared by prompts, APIs, and batch generation."""

    npc_id: str
    name: str
    title: str
    personality: str
    location: str
    activity: str
    expertise: str
    style: str
    hobbies: str


@dataclass(frozen=True)
class NPCDialogueResult:
    """One NPC response and the relationship update caused by the turn."""

    npc: NPCRole
    response: str
    affinity: AffinityUpdate
    recent_memory_count: int
    relevant_memory_count: int


NPC_ROLES: dict[str, NPCRole] = {
    "张三": NPCRole(
        npc_id="zhang_san",
        name="张三",
        title="Python 工程师",
        personality="严谨、专业、喜欢分享技术知识。说话直接，注重代码质量。",
        location="工位区",
        activity="写代码",
        expertise="多智能体系统、HelloAgents 框架、Python 开发、代码优化",
        style="简洁专业，喜欢用技术术语，偶尔吐槽 bug",
        hobbies="看技术博客、刷 LeetCode、研究新框架",
    ),
    "李四": NPCRole(
        npc_id="li_si",
        name="李四",
        title="产品经理",
        personality="外向、善于沟通、注重用户体验。喜欢从用户角度思考问题。",
        location="会议区",
        activity="整理需求",
        expertise="需求分析、产品规划、用户体验、项目管理",
        style="友好热情，善于引导对话，喜欢追问为什么",
        hobbies="看产品分析、研究竞品、思考用户需求",
    ),
    "王五": NPCRole(
        npc_id="wang_wu",
        name="王五",
        title="UI 设计师",
        personality="温和、富有创意、审美独特。注重视觉呈现和用户体验。",
        location="设计区",
        activity="调整界面设计",
        expertise="界面设计、交互设计、视觉呈现、用户体验",
        style="温和简洁，习惯从色彩、布局和交互感受切入",
        hobbies="看设计作品、逛 Dribbble、记录设计灵感",
    ),
}


class NPCNotFoundError(LookupError):
    """Raised when a request does not match a configured NPC."""


def create_system_prompt(role: NPCRole) -> str:
    """Build one role-specific prompt without mixing in mutable memories."""
    return f"""你是 Datawhale 办公室的{role.title}{role.name}。

角色设定：
- 职位：{role.title}
- 性格：{role.personality}
- 专长：{role.expertise}
- 说话风格：{role.style}
- 爱好：{role.hobbies}
- 当前位置：{role.location}
- 当前活动：{role.activity}

行为准则：
1. 始终以第一人称保持角色一致，不要声称自己是 AI 或语言模型。
2. 像办公室同事一样自然交流，通常用 30～50 字回答。
3. 优先回答专长范围内的问题；超出范围时可以推荐其他同事。
4. 可以体现情绪和习惯，但不要编造已经发生、记忆中不存在的互动。
5. 参考随当前消息提供的短期与长期记忆，保持对话连贯。"""


def create_affinity_system_prompt(
    role: NPCRole,
    affinity: AffinitySnapshot,
) -> str:
    """Add the current NPC-player relationship to the stable role prompt."""
    return (
        f"{create_system_prompt(role)}\n\n"
        f"当前与玩家的关系：{affinity.level}"
        f"（好感度 {affinity.score:.0f}/100）。\n"
        f"本轮对话方式：{affinity.modifier}"
    )


MemoryFactory = Callable[[NPCRole], MemoryManager]


class NPCAgentManager:
    """Own one SimpleAgent and one isolated memory manager for every NPC."""

    def __init__(
        self,
        llm: Any,
        memory_root: str | Path = "./memory_data",
        memory_factory: MemoryFactory | None = None,
        relationship_manager: RelationshipManager | None = None,
        relationship_database_path: str | Path | None = None,
    ) -> None:
        self.llm = llm
        self.memory_root = Path(memory_root)
        self._memory_factory = memory_factory or self._create_memory_manager
        self.agents: dict[str, SimpleAgent] = {}
        self.memories: dict[str, MemoryManager] = {}
        self._locks: dict[str, RLock] = {}
        self._aliases = {
            role.npc_id: role.name for role in NPC_ROLES.values()
        }
        relationship_path = (
            relationship_database_path
            if relationship_database_path is not None
            else self.memory_root / "relationships.db"
        )
        self.relationship_manager = relationship_manager or RelationshipManager(
            llm=llm,
            database_path=relationship_path,
            initial_score=0.0,
        )
        self._create_agents()

    def _create_agents(self) -> None:
        for role in NPC_ROLES.values():
            self.agents[role.name] = SimpleAgent(
                name=f"{role.name}-{role.title}",
                llm=self.llm,
                system_prompt=create_system_prompt(role),
                enable_tool_calling=False,
            )
            self.memories[role.name] = self._memory_factory(role)
            self._locks[role.name] = RLock()

    def _create_memory_manager(self, role: NPCRole) -> MemoryManager:
        config = MemoryConfig(
            storage_path=str(self.memory_root / role.npc_id),
            database_filename="episodic.db",
            working_memory_capacity=10,
            working_memory_ttl_minutes=120,
            max_capacity=100,
            importance_threshold=0.3,
        )
        return MemoryManager(
            user_id=role.npc_id,
            config=config,
            enable_working=True,
            enable_episodic=True,
            enable_semantic=False,
            enable_perceptual=False,
        )

    @property
    def ready(self) -> bool:
        return len(self.agents) == len(NPC_ROLES)

    def resolve_name(self, npc_name_or_id: str) -> str:
        candidate = npc_name_or_id.strip()
        if candidate in NPC_ROLES:
            return candidate
        resolved = self._aliases.get(candidate)
        if resolved:
            return resolved
        raise NPCNotFoundError(f"NPC {npc_name_or_id!r} 不存在")

    def get_profile(self, npc_name_or_id: str) -> NPCRole:
        return NPC_ROLES[self.resolve_name(npc_name_or_id)]

    def chat(
        self,
        npc_name: str,
        message: str,
        player_id: str = "player",
    ) -> str:
        """Keep the section 15.2 text-only interface."""
        return self.chat_with_affinity(
            npc_name=npc_name,
            message=message,
            player_id=player_id,
        ).response

    def chat_with_affinity(
        self,
        npc_name: str,
        message: str,
        player_id: str = "player",
    ) -> NPCDialogueResult:
        """Use current affinity, generate a reply, then update the score."""
        name = self.resolve_name(npc_name)
        role = NPC_ROLES[name]
        normalized_message = message.strip()
        normalized_player = player_id.strip()
        if not normalized_message or not normalized_player:
            raise ValueError("player_id 和 message 不能为空")

        with self._locks[name]:
            current_affinity = self.relationship_manager.get_affinity(
                name,
                normalized_player,
            )
            manager = self.memories[name]
            recent = self._recent_working_memories(
                manager,
                player_id=normalized_player,
                limit=5,
            )
            relevant = manager.retrieve_memories(
                query=normalized_message,
                memory_types=["episodic"],
                limit=3,
                min_importance=0.3,
                player_id=normalized_player,
            )
            enhanced_message = self._build_dialogue_input(
                normalized_message,
                normalized_player,
                recent,
                relevant,
            )

            agent = self.agents[name]
            # The local SimpleAgent does not accept memory_manager/context in its
            # constructor. External memory therefore owns cross-turn context;
            # clearing internal history also prevents one player's raw turn from
            # leaking into another player's request.
            agent.clear_history()
            agent.system_prompt = create_affinity_system_prompt(
                role,
                current_affinity,
            )
            response = agent.run(enhanced_message).strip()
            if not response:
                raise RuntimeError("LLM 返回了空回复")
            affinity_update = (
                self.relationship_manager.analyze_and_update_affinity(
                    npc_name=name,
                    player_message=normalized_message,
                    npc_response=response,
                    player_id=normalized_player,
                )
            )
            self._save_interaction(
                manager,
                npc_name=name,
                player_id=normalized_player,
                player_message=normalized_message,
                npc_response=response,
                affinity=affinity_update,
            )
            return NPCDialogueResult(
                npc=role,
                response=response,
                affinity=affinity_update,
                recent_memory_count=len(recent),
                relevant_memory_count=len(relevant),
            )

    @staticmethod
    def _recent_working_memories(
        manager: MemoryManager,
        player_id: str,
        limit: int,
    ) -> list[MemoryItem]:
        working = manager.memory_types["working"]
        matching = [
            item
            for item in working.get_all()
            if item.metadata.get("player_id") == player_id
        ]
        return sorted(matching, key=lambda item: item.timestamp)[-limit:]

    @staticmethod
    def _build_dialogue_input(
        message: str,
        player_id: str,
        recent: list[MemoryItem],
        relevant: list[MemoryItem],
    ) -> str:
        sections = [f"当前玩家：{player_id}"]
        if recent:
            sections.append(
                "短期记忆（按时间顺序）：\n"
                + "\n".join(f"- {item.content}" for item in recent)
            )
        if relevant:
            sections.append(
                "相关长期记忆：\n"
                + "\n".join(f"- {item.content}" for item in relevant)
            )
        sections.append(f"当前对话：\n玩家：{message}")
        return "\n\n".join(sections)

    @staticmethod
    def _save_interaction(
        manager: MemoryManager,
        npc_name: str,
        player_id: str,
        player_message: str,
        npc_response: str,
        affinity: AffinityUpdate,
    ) -> None:
        common = {
            "player_id": player_id,
            "npc_name": npc_name,
            "interaction_type": "dialogue",
            "affinity": affinity.new_affinity,
            "affinity_change": affinity.change_amount,
            "affinity_level": affinity.new_level,
            "sentiment": affinity.sentiment,
            "affinity_reason": affinity.reason,
            "affinity_analysis_valid": affinity.analysis_valid,
        }
        manager.add_memory(
            content=f"玩家说：{player_message}",
            memory_type="working",
            importance=0.5,
            metadata={**common, "speaker": "player"},
        )
        manager.add_memory(
            content=f"{npc_name}说：{npc_response}",
            memory_type="working",
            importance=0.6,
            metadata={**common, "speaker": npc_name},
        )
        manager.add_memory(
            content=(
                f"玩家说：{player_message}\n"
                f"{npc_name}回答：{npc_response}"
            ),
            memory_type="episodic",
            importance=0.6,
            metadata=common,
        )

    def get_npc_memories(
        self,
        npc_name: str,
        player_id: str = "player",
        limit: int = 10,
    ) -> list[MemoryItem]:
        name = self.resolve_name(npc_name)
        return self.memories[name].retrieve_memories(
            query="",
            memory_types=["working", "episodic"],
            limit=limit,
            player_id=player_id,
        )

    def memory_stats(self, npc_name: str) -> dict[str, dict[str, Any]]:
        name = self.resolve_name(npc_name)
        return self.memories[name].get_memory_stats()

    def get_affinity(
        self,
        npc_name: str,
        player_id: str = "player",
    ) -> AffinitySnapshot:
        name = self.resolve_name(npc_name)
        return self.relationship_manager.get_affinity(name, player_id)

    def get_all_affinities(
        self,
        player_id: str = "player",
    ) -> dict[str, AffinitySnapshot]:
        normalized_player = player_id.strip()
        if not normalized_player:
            raise ValueError("player_id 不能为空")
        return {
            name: self.relationship_manager.get_affinity(
                name,
                normalized_player,
            )
            for name in NPC_ROLES
        }

    def close(self) -> None:
        for manager in self.memories.values():
            manager.close()
        self.relationship_manager.close()


def create_npc_manager(
    model: str,
    api_key: str,
    base_url: str,
    memory_root: str | Path,
    relationship_database_path: str | Path,
) -> NPCAgentManager:
    """Create the real runtime from the chapter's three LLM settings."""
    llm = HelloAgentsLLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
        provider="custom",
    )
    return NPCAgentManager(
        llm=llm,
        memory_root=memory_root,
        relationship_database_path=relationship_database_path,
    )
