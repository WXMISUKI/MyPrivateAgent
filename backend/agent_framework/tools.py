"""Tool metadata for a reusable runtime layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple, Union


class ToolRenderMode(str, Enum):
    """How a tool result should be rendered by clients."""

    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    STRUCTURED_CARD = "structured_card"
    JSON = "json"


@dataclass(frozen=True)
class ToolSpec:
    """Runtime metadata for a tool."""

    name: str
    description: str
    permission_level: str = "auto"
    deterministic: bool = False
    safe_to_rephrase: bool = True
    render_mode: ToolRenderMode = ToolRenderMode.PLAIN_TEXT
    supports_cache: bool = False
    cache_ttl_seconds: Optional[float] = None
    timeout_seconds: Optional[float] = None
    passthrough_strategy: str = "never"
    card_schema: Optional[str] = None
    supported_card_schemas: Tuple[str, ...] = field(default_factory=tuple)
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["render_mode"] = self.render_mode.value
        return data


@dataclass(frozen=True)
class ArtifactRef:
    """Lightweight pointer to an artifact produced or associated with a tool run."""

    artifact_id: Optional[str] = None
    kind: str = "tool_result"
    uri: Optional[str] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        data = {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "uri": self.uri,
            "metadata": dict(self.metadata or {}),
        }
        return {key: value for key, value in data.items() if value not in (None, {}, "")}


@dataclass(frozen=True)
class ToolExecutionEnvelope:
    """Governable result contract emitted for every tool execution."""

    tool_name: str
    tool_call_id: Optional[str]
    status: str
    result_text: str
    render_mode: Optional[Union[ToolRenderMode, str]] = None
    card_schema: Optional[str] = None
    card: Optional[Dict[str, object]] = None
    artifact_ref: Optional[Union[ArtifactRef, Dict[str, object]]] = None
    execution_metadata: Dict[str, object] = field(default_factory=dict)
    tool_spec: Optional[Dict[str, object]] = None

    def to_dict(self) -> Dict[str, object]:
        render_mode = self.render_mode.value if isinstance(self.render_mode, ToolRenderMode) else self.render_mode
        artifact_ref = (
            self.artifact_ref.to_dict()
            if isinstance(self.artifact_ref, ArtifactRef)
            else dict(self.artifact_ref or {})
        )
        data = {
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
            "status": self.status,
            "result_text": self.result_text,
            "render_mode": render_mode,
            "card_schema": self.card_schema,
            "card": dict(self.card or {}),
            "artifact_ref": artifact_ref,
            "execution_metadata": dict(self.execution_metadata or {}),
            "tool_spec": dict(self.tool_spec or {}),
        }
        return {key: value for key, value in data.items() if value not in (None, {}, "")}
