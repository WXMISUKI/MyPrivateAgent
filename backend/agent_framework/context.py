"""Context and conversation history abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass
class ContextMessage:
    """Normalized context message."""

    role: str
    content: str
    created_at: Optional[datetime] = None
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ConversationContext(Protocol):
    """Single-conversation context window abstraction."""

    def add_user_message(self, content: str) -> Any:
        ...

    def add_assistant_message(self, content: str) -> Any:
        ...

    def add_system_message(self, content: str) -> Any:
        ...

    def get_messages(self) -> List[Dict[str, str]]:
        ...

    def get_stats(self) -> Dict[str, Any]:
        ...

    def clear(self) -> None:
        ...

    def is_empty(self) -> bool:
        ...


@runtime_checkable
class ContextStore(Protocol):
    """Multi-conversation context storage abstraction."""

    def get_context(self, conversation_id: int, model_name: Optional[str] = None) -> ConversationContext:
        ...

    def delete_context(self, conversation_id: int) -> None:
        ...

    def get_stats(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        ...
