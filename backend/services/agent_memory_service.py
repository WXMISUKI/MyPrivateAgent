"""Layered agent memory / instruction loader for the general agent framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AgentMemoryLayer:
    name: str
    path: str
    exists: bool
    content: str = ""


@dataclass(frozen=True)
class MemoryEntry:
    """Stable runtime contract for a recalled memory or instruction layer."""

    memory_id: str
    source: str
    scope: str
    content: str
    confidence: float
    retrieval_reason: str
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "source": self.source,
            "scope": self.scope,
            "content": self.content,
            "confidence": self.confidence,
            "retrieval_reason": self.retrieval_reason,
            "expires_at": self.expires_at,
        }


@dataclass
class AgentMemoryContext:
    system_prompt: str
    loaded_layers: List[AgentMemoryLayer] = field(default_factory=list)
    missing_layers: List[AgentMemoryLayer] = field(default_factory=list)
    memory_entries: List[MemoryEntry] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.loaded_layers


class AgentMemoryService:
    """Load layered instruction files similar to Claude Code style memory layers."""

    LAYER_FILES = (
        ("global", "GLOBAL_AGENT.md"),
        ("project", "PROJECT_AGENT.md"),
        ("local", "PROJECT_AGENT.local.md"),
        ("org_policy", "ORG_POLICY.md"),
    )

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parents[2]

    def build_context(self) -> AgentMemoryContext:
        loaded_layers: List[AgentMemoryLayer] = []
        missing_layers: List[AgentMemoryLayer] = []

        for layer_name, filename in self.LAYER_FILES:
            path = self.base_dir / filename
            if path.exists():
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    loaded_layers.append(
                        AgentMemoryLayer(
                            name=layer_name,
                            path=str(path),
                            exists=True,
                            content=content,
                        )
                    )
                    continue
            missing_layers.append(
                AgentMemoryLayer(
                    name=layer_name,
                    path=str(path),
                    exists=False,
                    content="",
                )
            )

        system_prompt = self._build_system_prompt(loaded_layers)
        memory_entries = [self._build_memory_entry(layer) for layer in loaded_layers]
        return AgentMemoryContext(
            system_prompt=system_prompt,
            loaded_layers=loaded_layers,
            missing_layers=missing_layers,
            memory_entries=memory_entries,
        )

    def build_runtime_contract(self) -> Dict[str, object]:
        context = self.build_context()
        return {
            "contract_version": "phase-b-memory-entry-v1",
            "loaded_layers": [
                {"name": item.name, "path": item.path}
                for item in context.loaded_layers
            ],
            "missing_layers": [
                {"name": item.name, "path": item.path}
                for item in context.missing_layers
            ],
            "memory_entries": [item.to_dict() for item in context.memory_entries],
            "layer_order": [name for name, _ in self.LAYER_FILES],
            "active": not context.is_empty,
        }

    def _build_memory_entry(self, layer: AgentMemoryLayer) -> MemoryEntry:
        return MemoryEntry(
            memory_id=f"memory:{layer.name}",
            source="agent_memory_layer",
            scope=layer.name,
            content=layer.content,
            confidence=1.0,
            retrieval_reason=f"loaded_layer:{layer.name}",
            expires_at=None,
        )

    def _build_system_prompt(self, loaded_layers: List[AgentMemoryLayer]) -> str:
        if not loaded_layers:
            return ""

        sections: List[str] = [
            "以下是当前运行时已加载的分层记忆 / 指令规则，请按层次共同遵守；越靠后的层可视为更贴近当前项目和本地环境的补充约束。"
        ]
        for layer in loaded_layers:
            sections.append(f"[{layer.name}] {Path(layer.path).name}\n{layer.content}")
        return "\n\n".join(sections)


_agent_memory_service: Optional[AgentMemoryService] = None


def get_agent_memory_service() -> AgentMemoryService:
    global _agent_memory_service
    if _agent_memory_service is None:
        _agent_memory_service = AgentMemoryService()
    return _agent_memory_service
