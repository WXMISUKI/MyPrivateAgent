"""Tool metadata for a reusable runtime layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


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
