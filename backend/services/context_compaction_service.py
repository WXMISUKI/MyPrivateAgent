"""Token-aware context window compaction for long conversations."""

from __future__ import annotations

import logging
from typing import Any, List

from langchain_core.messages import BaseMessage, SystemMessage

logger = logging.getLogger(__name__)

try:
    import tiktoken
    _encoder = tiktoken.get_encoding("cl100k_base")
    def _count(text: str) -> int:
        return len(_encoder.encode(text))
except ImportError:
    def _count(text: str) -> int:
        return len(text) // 4


class ContextCompactionService:
    def __init__(self, max_tokens: int = 8000, reserve_recent: int = 6):
        self.max_tokens = max_tokens
        self.reserve_recent = reserve_recent

    def count_tokens(self, text: str) -> int:
        return _count(text)

    def _message_tokens(self, msg: BaseMessage) -> int:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        return _count(content) + 4

    def compact(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        total = sum(self._message_tokens(m) for m in messages)
        if total <= self.max_tokens:
            return list(messages)

        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        non_system = [m for m in messages if not isinstance(m, SystemMessage)]

        system_tokens = sum(self._message_tokens(m) for m in system_msgs)
        budget = self.max_tokens - system_tokens

        if budget <= 0:
            logger.warning("System messages alone exceed token budget")
            return system_msgs

        kept: list[BaseMessage] = []
        used = 0
        for msg in reversed(non_system):
            msg_tokens = self._message_tokens(msg)
            if used + msg_tokens > budget:
                break
            kept.insert(0, msg)
            used += msg_tokens

        if not kept and non_system:
            kept = non_system[-self.reserve_recent:]

        logger.info(
            "Context compacted: %d -> %d messages (%d -> ~%d tokens)",
            len(messages), len(system_msgs) + len(kept), total, system_tokens + used,
        )
        return system_msgs + kept


_instance: ContextCompactionService | None = None

def get_context_compaction_service() -> ContextCompactionService:
    global _instance
    if _instance is None:
        _instance = ContextCompactionService()
    return _instance
