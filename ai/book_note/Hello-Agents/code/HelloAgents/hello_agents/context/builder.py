"""Build compact model context with the chapter's GSSC pipeline."""

from __future__ import annotations

import math
import re
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Sequence

from ..core.message import Message


@dataclass
class ContextPacket:
    """One candidate piece of information considered for the context."""

    content: str
    timestamp: datetime
    token_count: int
    relevance_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("ContextPacket.content 不能为空")
        if not isinstance(self.timestamp, datetime):
            raise TypeError("ContextPacket.timestamp 必须是 datetime")
        if self.token_count < 0:
            raise ValueError("ContextPacket.token_count 不能为负数")
        self.relevance_score = max(
            0.0,
            min(1.0, float(self.relevance_score)),
        )
        self.metadata = dict(self.metadata or {})


@dataclass
class ContextConfig:
    """Configuration for context selection and budget protection."""

    max_tokens: int = 3000
    reserve_ratio: float = 0.2
    min_relevance: float = 0.1
    enable_compression: bool = True
    recency_weight: float = 0.3
    relevance_weight: float = 0.7

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0")
        if not 0.0 <= self.reserve_ratio <= 1.0:
            raise ValueError("reserve_ratio 必须在 [0, 1] 范围内")
        if not 0.0 <= self.min_relevance <= 1.0:
            raise ValueError("min_relevance 必须在 [0, 1] 范围内")
        if not 0.0 <= self.recency_weight <= 1.0:
            raise ValueError("recency_weight 必须在 [0, 1] 范围内")
        if not 0.0 <= self.relevance_weight <= 1.0:
            raise ValueError("relevance_weight 必须在 [0, 1] 范围内")
        if not math.isclose(
            self.recency_weight + self.relevance_weight,
            1.0,
            abs_tol=1e-6,
        ):
            raise ValueError(
                "recency_weight + relevance_weight 必须等于 1.0",
            )


class ContextBuilder:
    """Gather, select, structure, and compress information for one call."""

    _EVIDENCE_TYPES = {"rag_result", "knowledge"}
    _STATE_TYPES = {"state", "task_state"}

    def __init__(
        self,
        memory_tool: Any | None = None,
        rag_tool: Any | None = None,
        config: ContextConfig | None = None,
    ) -> None:
        self.memory_tool = memory_tool
        self.rag_tool = rag_tool
        self.config = config or ContextConfig()

    def build(
        self,
        user_query: str,
        conversation_history: Sequence[Message] | None = None,
        system_instructions: str | None = None,
        custom_packets: Sequence[ContextPacket] | None = None,
    ) -> str:
        """Run the complete GSSC pipeline and return one prompt string."""
        query = user_query.strip()
        if not query:
            raise ValueError("user_query 不能为空")

        packets = self._gather(
            user_query=query,
            conversation_history=conversation_history,
            system_instructions=system_instructions,
            custom_packets=custom_packets,
        )
        selected = self._select(
            packets,
            user_query=query,
            available_tokens=self.config.max_tokens,
        )
        context = self._structure(selected, query)
        if self.config.enable_compression:
            context = self._compress(context, self.config.max_tokens)
        return context

    def _gather(
        self,
        user_query: str,
        conversation_history: Sequence[Message] | None = None,
        system_instructions: str | None = None,
        custom_packets: Sequence[ContextPacket] | None = None,
    ) -> List[ContextPacket]:
        """Collect candidates from instructions, memory, RAG, and history."""
        packets: List[ContextPacket] = []

        if system_instructions and system_instructions.strip():
            content = system_instructions.strip()
            packets.append(
                ContextPacket(
                    content=content,
                    timestamp=datetime.now(),
                    token_count=self._count_tokens(content),
                    relevance_score=1.0,
                    metadata={
                        "type": "system_instruction",
                        "priority": "high",
                    },
                ),
            )

        if self.memory_tool is not None:
            try:
                packets.extend(self._memory_packets(user_query))
            except Exception as error:
                warnings.warn(
                    f"记忆检索失败：{error}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        if self.rag_tool is not None:
            try:
                packets.extend(self._rag_packets(user_query))
            except Exception as error:
                warnings.warn(
                    f"RAG 检索失败：{error}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        if conversation_history:
            for message in conversation_history[-5:]:
                content = f"{message.role}: {message.content}"
                packets.append(
                    ContextPacket(
                        content=content,
                        timestamp=message.timestamp,
                        token_count=self._count_tokens(content),
                        relevance_score=0.6,
                        metadata={
                            "type": "conversation_history",
                            "role": message.role,
                        },
                    ),
                )

        for packet in custom_packets or ():
            if not isinstance(packet, ContextPacket):
                raise TypeError("custom_packets 中的元素必须是 ContextPacket")
            if packet.token_count == 0:
                packet.token_count = self._count_tokens(packet.content)
            packets.append(packet)

        return packets

    def _memory_packets(self, user_query: str) -> List[ContextPacket]:
        """Retrieve memory while preserving structured fields when possible."""
        manager = getattr(self.memory_tool, "manager", None)
        if manager is not None and hasattr(manager, "retrieve_memories"):
            memories = manager.retrieve_memories(
                query=user_query,
                limit=10,
                min_importance=0.3,
            )
            packets = []
            for memory in memories:
                content = f"记忆：{memory.content}"
                score = memory.metadata.get("_retrieval_score")
                relevance = (
                    self._calculate_relevance(content, user_query)
                    if score is None
                    else max(0.0, min(1.0, float(score)))
                )
                packets.append(
                    ContextPacket(
                        content=content,
                        timestamp=memory.timestamp,
                        token_count=self._count_tokens(content),
                        relevance_score=relevance,
                        metadata={
                            "type": "memory_result",
                            "memory_type": memory.memory_type,
                            "memory_id": memory.id,
                        },
                    ),
                )
            return packets

        result = self.memory_tool.run(
            {
                "action": "search",
                "query": user_query,
                "limit": 10,
                "min_importance": 0.3,
            },
        )
        return self._text_result_packet(
            result,
            user_query,
            packet_type="memory_result",
        )

    def _rag_packets(self, user_query: str) -> List[ContextPacket]:
        """Retrieve knowledge while preserving scores and citations."""
        if hasattr(self.rag_tool, "search_results"):
            results = self.rag_tool.search_results(
                user_query,
                limit=5,
                min_score=0.3,
                enable_advanced_search=False,
            )
            packets = []
            for result in results:
                metadata = dict(result.get("metadata") or {})
                content = str(
                    result.get("content") or metadata.get("content") or "",
                ).strip()
                if not content:
                    continue
                source = metadata.get("source_name") or metadata.get(
                    "source_path",
                )
                heading = metadata.get("heading_path")
                if source:
                    citation = f"来源：{source}"
                    if heading:
                        citation += f" > {heading}"
                    content = f"{content}\n{citation}"
                score = result.get("score")
                relevance = (
                    self._calculate_relevance(content, user_query)
                    if score is None
                    else max(0.0, min(1.0, float(score)))
                )
                packets.append(
                    ContextPacket(
                        content=content,
                        timestamp=self._coerce_timestamp(
                            metadata.get("updated_at")
                            or metadata.get("created_at"),
                        ),
                        token_count=self._count_tokens(content),
                        relevance_score=relevance,
                        metadata={
                            **metadata,
                            "type": "rag_result",
                        },
                    ),
                )
            return packets

        result = self.rag_tool.run(
            {
                "action": "search",
                "query": user_query,
                "limit": 5,
                "min_score": 0.3,
            },
        )
        return self._text_result_packet(
            result,
            user_query,
            packet_type="rag_result",
        )

    def _text_result_packet(
        self,
        result: Any,
        user_query: str,
        packet_type: str,
    ) -> List[ContextPacket]:
        text = str(result or "").strip()
        if not text or text.startswith(("错误：", "未找到")):
            return []
        return [
            ContextPacket(
                content=text,
                timestamp=datetime.now(),
                token_count=self._count_tokens(text),
                relevance_score=self._calculate_relevance(text, user_query),
                metadata={"type": packet_type},
            ),
        ]

    def _select(
        self,
        packets: Sequence[ContextPacket],
        user_query: str,
        available_tokens: int,
    ) -> List[ContextPacket]:
        """Rank candidates by relevance and recency, then fill the budget."""
        system_packets = [
            packet
            for packet in packets
            if packet.metadata.get("type") == "system_instruction"
        ]
        other_packets = [
            packet
            for packet in packets
            if packet.metadata.get("type") != "system_instruction"
        ]

        system_tokens = sum(packet.token_count for packet in system_packets)
        reserved_tokens = math.ceil(
            available_tokens * self.config.reserve_ratio,
        )
        content_budget = max(
            0,
            available_tokens - max(system_tokens, reserved_tokens),
        )

        scored_packets: List[tuple[float, ContextPacket]] = []
        for packet in other_packets:
            if packet.relevance_score == 0.5:
                packet.relevance_score = self._calculate_relevance(
                    packet.content,
                    user_query,
                )
            if packet.relevance_score < self.config.min_relevance:
                continue
            recency = self._calculate_recency(packet.timestamp)
            score = (
                self.config.relevance_weight * packet.relevance_score
                + self.config.recency_weight * recency
            )
            scored_packets.append((score, packet))

        scored_packets.sort(key=lambda item: item[0], reverse=True)
        selected = list(system_packets)
        used_content_tokens = 0
        for _, packet in scored_packets:
            if used_content_tokens + packet.token_count > content_budget:
                continue
            selected.append(packet)
            used_content_tokens += packet.token_count
        return selected

    def _calculate_relevance(self, content: str, query: str) -> float:
        """Estimate relevance with the chapter's lightweight overlap rule."""
        content_terms = self._terms(content)
        query_terms = self._terms(query)
        if not query_terms:
            return 0.0
        union = content_terms | query_terms
        return len(content_terms & query_terms) / len(union) if union else 0.0

    @staticmethod
    def _terms(text: str) -> set[str]:
        normalized = text.lower()
        latin_terms = set(re.findall(r"[a-z0-9_]+", normalized))
        chinese_terms = {
            character
            for character in normalized
            if "\u4e00" <= character <= "\u9fff"
        }
        return latin_terms | chinese_terms

    @staticmethod
    def _calculate_recency(timestamp: datetime) -> float:
        """Apply exponential decay while remaining safe for aware datetimes."""
        now = (
            datetime.now(timestamp.tzinfo)
            if timestamp.tzinfo is not None
            else datetime.now()
        )
        age_hours = max(0.0, (now - timestamp).total_seconds() / 3600)
        score = math.exp(-0.1 * age_hours / 24)
        return max(0.1, min(1.0, score))

    def _structure(
        self,
        selected_packets: Sequence[ContextPacket],
        user_query: str,
    ) -> str:
        """Organize selected packets into the chapter's stable skeleton."""
        roles: List[str] = []
        states: List[str] = []
        evidence: List[str] = []
        history: List[tuple[datetime, str]] = []
        context: List[str] = []

        for packet in selected_packets:
            packet_type = packet.metadata.get("type", "general")
            if packet_type == "system_instruction":
                roles.append(packet.content)
            elif packet_type in self._STATE_TYPES:
                states.append(packet.content)
            elif packet_type in self._EVIDENCE_TYPES:
                evidence.append(packet.content)
            elif packet_type == "conversation_history":
                history.append((packet.timestamp, packet.content))
            else:
                context.append(packet.content)

        history.sort(key=lambda item: item[0].timestamp())
        context = [content for _, content in history] + context

        sections: List[str] = []
        if roles:
            sections.append("[Role & Policies]\n" + "\n".join(roles))
        sections.append(f"[Task]\n{user_query}")
        if states:
            sections.append("[State]\n" + "\n".join(states))
        if evidence:
            sections.append("[Evidence]\n" + "\n---\n".join(evidence))
        if context:
            sections.append("[Context]\n" + "\n".join(context))
        sections.append(
            "[Output]\n请基于以上信息，提供准确、有据的回答。",
        )
        return "\n\n".join(sections)

    def _compress(self, context: str, max_tokens: int) -> str:
        """Truncate section bodies while retaining the fixed skeleton."""
        if self._count_tokens(context) <= max_tokens:
            return context

        sections = self._split_sections(context)
        if not sections:
            return self._truncate_text(context, max_tokens)

        empty_skeleton = "\n\n".join(
            f"[{title}]\n" for title, _ in sections
        )
        remaining = max(0, max_tokens - self._count_tokens(empty_skeleton))
        allocations = {title: 0 for title, _ in sections}
        bodies = {title: body for title, body in sections}

        # Preserve output and task before role text, then spend the remaining
        # budget on the optional sections in their original order.
        order = ["Output", "Task", "Role & Policies"]
        order.extend(
            title
            for title, _ in sections
            if title not in order
        )
        for title in order:
            if title not in bodies or remaining <= 0:
                continue
            needed = self._count_tokens(bodies[title])
            allocation = min(needed, remaining)
            allocations[title] = allocation
            remaining -= allocation

        compressed = []
        for title, body in sections:
            allocation = allocations[title]
            needed = self._count_tokens(body)
            if allocation < needed:
                marker = "\n[... 内容已压缩 ...]"
                marker_tokens = self._count_tokens(marker)
                body_budget = max(0, allocation - marker_tokens)
                selected_body = self._truncate_text(body, body_budget)
                if allocation >= marker_tokens:
                    selected_body = selected_body.rstrip() + marker
            else:
                selected_body = body
            compressed.append(f"[{title}]\n{selected_body}".rstrip())

        result = "\n\n".join(compressed)
        if self._count_tokens(result) > max_tokens:
            return self._truncate_text(result, max_tokens)
        return result

    @staticmethod
    def _split_sections(context: str) -> List[tuple[str, str]]:
        matches = list(
            re.finditer(
                (
                    r"(?m)^\[(Role & Policies|Task|State|Evidence|Context|"
                    r"Output)\]\n?"
                ),
                context,
            ),
        )
        sections = []
        for index, match in enumerate(matches):
            start = match.end()
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(context)
            )
            sections.append(
                (match.group(1), context[start:end].strip()),
            )
        return sections

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate by character boundary using the local token estimator."""
        if max_tokens <= 0:
            return ""
        if self._count_tokens(text) <= max_tokens:
            return text
        low, high = 0, len(text)
        while low < high:
            middle = (low + high + 1) // 2
            if self._count_tokens(text[:middle]) <= max_tokens:
                low = middle
            else:
                high = middle - 1
        return text[:low].rstrip()

    @staticmethod
    def _count_tokens(text: str) -> int:
        """Estimate tokens without adding a tokenizer dependency."""
        if not text or not text.strip():
            return 0
        chinese_chars = sum(
            1 for character in text if "\u4e00" <= character <= "\u9fff"
        )
        latin_words = len(re.findall(r"[A-Za-z0-9_]+", text))
        remaining_chars = sum(
            1
            for character in text
            if not character.isspace()
            and not "\u4e00" <= character <= "\u9fff"
            and not character.isalnum()
            and character != "_"
        )
        return max(
            1,
            chinese_chars
            + math.ceil(latin_words * 1.3)
            + math.ceil(remaining_chars / 4),
        )

    @staticmethod
    def _coerce_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now()
