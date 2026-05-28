"""Build bounded model input from persisted chat history."""

from __future__ import annotations

from typing import Any, Iterable, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

try:
    import tiktoken

    _encoder = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(text: str) -> int:
        return len(_encoder.encode(text))

except ImportError:  # pragma: no cover - dependency is present in normal backend env

    def _count_tokens(text: str) -> int:
        return max(1, len(text) // 4)


class ChatContextPackingService:
    """Pack durable conversation messages into a bounded LangChain message list."""

    BUDGET_OVERFLOW_TOLERANCE = 32
    SUMMARY_EXCERPT_CHARS = 80

    def __init__(self, max_tokens: int = 8000, reserve_recent: int = 8):
        self.max_tokens = max_tokens
        self.reserve_recent = reserve_recent

    def pack(
        self,
        *,
        system_messages: Sequence[BaseMessage],
        history_messages: Sequence[Any] | None,
        current_user_message: str,
        durable_summary: Any | None = None,
    ) -> List[BaseMessage]:
        systems = list(system_messages or [])
        current = HumanMessage(content=str(current_user_message or ""))
        normalized_history = self._normalize_history(history_messages or [], current.content)

        recent_count = max(0, self.reserve_recent)
        older = normalized_history[:-recent_count] if recent_count else normalized_history
        recent = normalized_history[-recent_count:] if recent_count else []

        conversation_candidates: list[BaseMessage] = []
        summary = self._build_durable_summary(durable_summary) or self._build_summary(older)
        if summary:
            conversation_candidates.append(SystemMessage(content=summary))
        conversation_candidates.extend(recent)
        conversation_candidates.append(current)

        budget = max(0, self.max_tokens - self.estimate_messages_tokens(systems))
        packed_conversation = self._fit_conversation_to_budget(conversation_candidates, budget)
        return systems + packed_conversation

    def estimate_messages_tokens(self, messages: Iterable[BaseMessage]) -> int:
        return sum(self._message_tokens(message) for message in messages)

    def _message_tokens(self, message: BaseMessage) -> int:
        content = message.content if isinstance(message.content, str) else str(message.content)
        return _count_tokens(content) + 4

    def _normalize_history(self, history_messages: Sequence[Any], current_user_message: str) -> list[BaseMessage]:
        normalized: list[BaseMessage] = []
        for raw in history_messages:
            role = str(getattr(raw, "role", "") or "").strip().lower()
            content = str(getattr(raw, "content", "") or "")
            if not content:
                continue
            if role == "assistant":
                normalized.append(AIMessage(content=content))
            elif role == "system":
                normalized.append(SystemMessage(content=content))
            else:
                normalized.append(HumanMessage(content=content))

        if normalized:
            last = normalized[-1]
            if isinstance(last, HumanMessage) and str(last.content or "") == current_user_message:
                normalized = normalized[:-1]
        return normalized

    def _build_summary(self, messages: Sequence[BaseMessage]) -> str:
        if not messages:
            return ""

        user_excerpt = self._first_excerpt(messages, HumanMessage)
        assistant_excerpt = self._first_excerpt(messages, AIMessage)
        parts = [f"[早期对话摘要] 已压缩 {len(messages)} 条较早会话消息。"]
        if user_excerpt:
            parts.append(f"较早用户内容示例：{user_excerpt}")
        if assistant_excerpt:
            parts.append(f"较早助手内容示例：{assistant_excerpt}")
        return " ".join(parts)

    def _build_durable_summary(self, durable_summary: Any | None) -> str:
        if durable_summary is None:
            return ""
        text = str(getattr(durable_summary, "summary", "") or "").strip()
        if not text:
            return ""
        message_count = getattr(durable_summary, "message_count", None)
        prefix = "[持久化对话摘要]"
        if message_count is not None:
            prefix += f" 已覆盖 {message_count} 条历史消息。"
        return f"{prefix} {text}".strip()

    def _first_excerpt(self, messages: Sequence[BaseMessage], message_type: type[BaseMessage]) -> str:
        for message in messages:
            if isinstance(message, message_type):
                return self._excerpt(str(message.content or ""))
        return ""

    def _excerpt(self, text: str) -> str:
        compact = " ".join(str(text or "").split())
        if len(compact) <= self.SUMMARY_EXCERPT_CHARS:
            return compact
        return compact[: self.SUMMARY_EXCERPT_CHARS - 3].rstrip() + "..."

    def _fit_conversation_to_budget(self, messages: Sequence[BaseMessage], budget: int) -> list[BaseMessage]:
        if not messages:
            return []
        if budget <= 0:
            return [messages[-1]]
        if self.estimate_messages_tokens(messages) <= budget + self.BUDGET_OVERFLOW_TOLERANCE:
            return list(messages)

        summary_messages = [m for m in messages[:-1] if isinstance(m, SystemMessage)]
        current = messages[-1]
        kept: list[BaseMessage] = [current]
        used = self.estimate_messages_tokens(kept)
        summary_tokens = self.estimate_messages_tokens(summary_messages)

        for message in reversed([m for m in messages[:-1] if not isinstance(m, SystemMessage)]):
            message_tokens = self._message_tokens(message)
            if used + summary_tokens + message_tokens > budget + self.BUDGET_OVERFLOW_TOLERANCE:
                continue
            kept.insert(0, message)
            used += message_tokens

        if summary_messages and used + summary_tokens <= budget + self.BUDGET_OVERFLOW_TOLERANCE:
            return summary_messages + kept
        return kept


_instance: ChatContextPackingService | None = None


def get_chat_context_packing_service() -> ChatContextPackingService:
    global _instance
    if _instance is None:
        _instance = ChatContextPackingService()
    return _instance
