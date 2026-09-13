"""Persistent NPC-player affinity management for section 15.3."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Literal


FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
if str(FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK_ROOT))

from hello_agents import SimpleAgent  # noqa: E402


AffinityLevel = Literal["陌生", "熟悉", "友好", "亲密", "挚友"]
Sentiment = Literal["positive", "neutral", "negative"]


AFFINITY_MODIFIERS: dict[AffinityLevel, str] = {
    "陌生": "刚认识这位玩家，保持礼貌和距离，回复简短专业。",
    "熟悉": "已经认识这位玩家，可以正常交流，回复自然友好。",
    "友好": "把这位玩家当作朋友，愿意分享更多信息，回复热情一些。",
    "亲密": "非常信任这位玩家，可以表达关心，并分享较私人的话题。",
    "挚友": "把这位玩家当作最好的朋友，回复亲切真诚，可以坦率交流。",
}


@dataclass(frozen=True)
class AffinityAnalysis:
    should_change: bool
    change_amount: int
    reason: str
    sentiment: Sentiment
    valid: bool = True


@dataclass(frozen=True)
class AffinitySnapshot:
    npc_name: str
    player_id: str
    score: float
    level: AffinityLevel
    modifier: str
    interaction_count: int
    updated_at: str | None


@dataclass(frozen=True)
class AffinityUpdate:
    npc_name: str
    player_id: str
    changed: bool
    old_affinity: float
    new_affinity: float
    change_amount: int
    reason: str
    sentiment: Sentiment
    old_level: AffinityLevel
    new_level: AffinityLevel
    interaction_count: int
    analysis_valid: bool


class RelationshipManager:
    """Analyze dialogue and persist one score for each NPC-player pair."""

    def __init__(
        self,
        llm: Any,
        database_path: str | Path = "./data/cyber_town.db",
        initial_score: float = 0.0,
    ) -> None:
        self.llm = llm
        self.initial_score = self._clamp_score(initial_score)
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).expanduser().parent.mkdir(
                parents=True,
                exist_ok=True,
            )
        self._db_lock = RLock()
        self._analyzer_lock = RLock()
        self._connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._initialize()
        self.analyzer_agent = SimpleAgent(
            name="AffinityAnalyzer",
            llm=llm,
            system_prompt=self._create_analyzer_prompt(),
            enable_tool_calling=False,
        )

    def _initialize(self) -> None:
        with self._db_lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS affinity_relationships (
                    npc_name TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    interaction_count INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (npc_name, player_id)
                )
                """,
            )

    @staticmethod
    def _create_analyzer_prompt() -> str:
        return """你负责判断一轮 NPC 对话是否应改变好感度。

分析玩家态度、内容、互动质量和情感倾向，并遵守以下规则：
- 赞美、感谢、请教：+3 到 +8；
- 友好问候、正常交流：+1 到 +3；
- 普通闲聊、中性话题：0；
- 批评、质疑、不耐烦：-3 到 -8；
- 侮辱、攻击、恶意：-8 到 -15。

只返回 JSON：
{
  "should_change": true,
  "change_amount": 5,
  "reason": "友好问候",
  "sentiment": "positive"
}

约束：change_amount 必须是 -15 到 +10 的整数；不改变时必须为 0；
reason 不超过 10 个字；sentiment 只能是 positive、neutral、negative。"""

    def analyze_dialogue(
        self,
        npc_name: str,
        player_message: str,
        npc_response: str,
    ) -> AffinityAnalysis:
        prompt = (
            "请分析以下对话：\n"
            f"玩家：{player_message}\n"
            f"{npc_name}：{npc_response}"
        )
        try:
            with self._analyzer_lock:
                self.analyzer_agent.clear_history()
                response = self.analyzer_agent.run(prompt)
            return self.parse_analysis(response)
        except Exception:
            return self.invalid_analysis("分析调用失败")

    @classmethod
    def parse_analysis(cls, response: str) -> AffinityAnalysis:
        raw = response.strip()
        if raw.startswith("```") and raw.endswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1]).strip()
        if not raw.startswith("{"):
            start, end = raw.find("{"), raw.rfind("}")
            if start >= 0 and end > start:
                raw = raw[start : end + 1]

        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return cls.invalid_analysis("解析失败")
        if not isinstance(value, dict):
            return cls.invalid_analysis("格式错误")

        should_change = value.get("should_change")
        change_amount = value.get("change_amount")
        reason = value.get("reason")
        sentiment = value.get("sentiment")
        valid = (
            isinstance(should_change, bool)
            and isinstance(change_amount, int)
            and not isinstance(change_amount, bool)
            and -15 <= change_amount <= 10
            and isinstance(reason, str)
            and bool(reason.strip())
            and len(reason.strip()) <= 10
            and sentiment in {"positive", "neutral", "negative"}
            and (should_change or change_amount == 0)
        )
        if not valid:
            return cls.invalid_analysis("格式错误")
        return AffinityAnalysis(
            should_change=should_change,
            change_amount=change_amount if should_change else 0,
            reason=reason.strip(),
            sentiment=sentiment,
        )

    @staticmethod
    def invalid_analysis(reason: str) -> AffinityAnalysis:
        return AffinityAnalysis(
            should_change=False,
            change_amount=0,
            reason=reason,
            sentiment="neutral",
            valid=False,
        )

    def analyze_and_update_affinity(
        self,
        npc_name: str,
        player_message: str,
        npc_response: str,
        player_id: str = "player",
    ) -> AffinityUpdate:
        analysis = self.analyze_dialogue(
            npc_name=npc_name,
            player_message=player_message,
            npc_response=npc_response,
        )
        with self._db_lock:
            current = self.get_affinity(npc_name, player_id)
            requested_change = (
                analysis.change_amount if analysis.should_change else 0
            )
            updated_score = self._clamp_score(current.score + requested_change)
            interaction_count = current.interaction_count + 1
            updated_at = datetime.now(timezone.utc).isoformat()
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO affinity_relationships(
                        npc_name, player_id, score,
                        interaction_count, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(npc_name, player_id) DO UPDATE SET
                        score = excluded.score,
                        interaction_count = excluded.interaction_count,
                        updated_at = excluded.updated_at
                    """,
                    (
                        npc_name,
                        player_id,
                        updated_score,
                        interaction_count,
                        updated_at,
                    ),
                )

        old_level = self.get_affinity_level(current.score)
        new_level = self.get_affinity_level(updated_score)
        return AffinityUpdate(
            npc_name=npc_name,
            player_id=player_id,
            changed=updated_score != current.score,
            old_affinity=current.score,
            new_affinity=updated_score,
            change_amount=int(updated_score - current.score),
            reason=analysis.reason,
            sentiment=analysis.sentiment,
            old_level=old_level,
            new_level=new_level,
            interaction_count=interaction_count,
            analysis_valid=analysis.valid,
        )

    def get_affinity(
        self,
        npc_name: str,
        player_id: str = "player",
    ) -> AffinitySnapshot:
        with self._db_lock:
            row = self._connection.execute(
                """
                SELECT score, interaction_count, updated_at
                FROM affinity_relationships
                WHERE npc_name = ? AND player_id = ?
                """,
                (npc_name, player_id),
            ).fetchone()
        score = float(row["score"]) if row else self.initial_score
        level = self.get_affinity_level(score)
        return AffinitySnapshot(
            npc_name=npc_name,
            player_id=player_id,
            score=score,
            level=level,
            modifier=AFFINITY_MODIFIERS[level],
            interaction_count=int(row["interaction_count"]) if row else 0,
            updated_at=str(row["updated_at"]) if row else None,
        )

    def set_affinity(
        self,
        npc_name: str,
        affinity: float,
        player_id: str = "player",
    ) -> AffinitySnapshot:
        score = self._clamp_score(affinity)
        with self._db_lock:
            current = self.get_affinity(npc_name, player_id)
            updated_at = datetime.now(timezone.utc).isoformat()
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO affinity_relationships(
                        npc_name, player_id, score,
                        interaction_count, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(npc_name, player_id) DO UPDATE SET
                        score = excluded.score,
                        updated_at = excluded.updated_at
                    """,
                    (
                        npc_name,
                        player_id,
                        score,
                        current.interaction_count,
                        updated_at,
                    ),
                )
        return self.get_affinity(npc_name, player_id)

    def get_all_affinities(
        self,
        player_id: str = "player",
    ) -> dict[str, AffinitySnapshot]:
        with self._db_lock:
            rows = self._connection.execute(
                """
                SELECT npc_name FROM affinity_relationships
                WHERE player_id = ? ORDER BY npc_name
                """,
                (player_id,),
            ).fetchall()
        return {
            str(row["npc_name"]): self.get_affinity(
                str(row["npc_name"]),
                player_id,
            )
            for row in rows
        }

    @staticmethod
    def get_affinity_level(score: float) -> AffinityLevel:
        normalized = RelationshipManager._clamp_score(score)
        if normalized <= 20:
            return "陌生"
        if normalized <= 40:
            return "熟悉"
        if normalized <= 60:
            return "友好"
        if normalized <= 80:
            return "亲密"
        return "挚友"

    @staticmethod
    def get_affinity_modifier(score: float) -> str:
        return AFFINITY_MODIFIERS[
            RelationshipManager.get_affinity_level(score)
        ]

    @staticmethod
    def _clamp_score(score: float) -> float:
        return max(0.0, min(100.0, float(score)))

    def close(self) -> None:
        with self._db_lock:
            self._connection.close()
