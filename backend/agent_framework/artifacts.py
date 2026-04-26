"""Artifact storage abstractions for tool outputs and runtime side-products."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass
class Artifact:
    """Structured runtime artifact."""

    artifact_id: str
    conversation_id: Optional[int]
    kind: str
    content: str
    created_at: datetime
    render_mode: Optional[str] = None
    card_schema: Optional[str] = None
    card: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ArtifactStore(Protocol):
    """Artifact persistence abstraction."""

    def create_artifact(
        self,
        *,
        conversation_id: Optional[int],
        kind: str,
        content: str,
        render_mode: Optional[str] = None,
        card_schema: Optional[str] = None,
        card: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        ...

    def list_artifacts(self, conversation_id: Optional[int] = None, kind: Optional[str] = None) -> List[Artifact]:
        ...
