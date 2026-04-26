"""Session memory abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@dataclass
class SessionRecord:
    """Normalized session information."""

    conversation_id: int
    state: str
    created_at: datetime
    last_active: datetime
    message_count: int = 0
    total_tokens: int = 0
    user_id: Optional[int] = None
    model_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SessionStore(Protocol):
    """Session lifecycle abstraction."""

    def create_session(self, conversation_id: int, user_id: Optional[int] = None, model_name: Optional[str] = None) -> SessionRecord:
        ...

    def get_session(self, conversation_id: int) -> Optional[SessionRecord]:
        ...

    def update_session_activity(self, conversation_id: int) -> None:
        ...

    def increment_message_count(self, conversation_id: int) -> None:
        ...

    def update_tokens(self, conversation_id: int, tokens: int) -> None:
        ...

    def get_stats(self) -> Dict[str, Any]:
        ...
