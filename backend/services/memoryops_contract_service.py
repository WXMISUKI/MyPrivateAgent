"""MemoryOps lifecycle read model for existing memory and summary services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


MEMORYOPS_CONTRACT_VERSION = "agent-memoryops-lifecycle-v1"
MEMORYOPS_REGISTRY_CONTRACT_VERSION = "agent-memoryops-registry-v1"

MEMORY_KIND_RUNTIME_INSTRUCTION = "runtime_instruction_memory"
MEMORY_KIND_CONVERSATION_SUMMARY = "conversation_summary"

STATUS_ACTIVE = "active"
TTL_NONE = "none"


@dataclass(frozen=True)
class MemoryOpsContractService:
    """Builds a side-effect-free MemoryOps lifecycle registry."""

    def build_registry(
        self,
        *,
        agent_memory_contract: Optional[Dict[str, Any]] = None,
        conversation_summary: Optional[Any] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        entries: List[Dict[str, Any]] = []
        entries.extend(self._instruction_entries(agent_memory_contract or {}))
        summary_entry = self._conversation_summary_entry(conversation_summary)
        if summary_entry is not None:
            entries.append(summary_entry)

        active_count = sum(1 for entry in entries if entry.get("status") == STATUS_ACTIVE)
        return {
            "contract_version": MEMORYOPS_REGISTRY_CONTRACT_VERSION,
            "memoryops_contract_version": MEMORYOPS_CONTRACT_VERSION,
            "conversation_id": conversation_id,
            "entry_count": len(entries),
            "active_entry_count": active_count,
            "behavior_boundary": {
                "mode": "visibility_only",
                "chat_context_packing_changed": False,
                "prompt_injection_changed": False,
                "retrieval_behavior_changed": False,
            },
            "posture": {
                "hot_session_state": {
                    "available": False,
                    "status": "not_implemented",
                    "reason": "no_memoryops_hot_session_store",
                },
                "long_term_memory": {
                    "available": False,
                    "status": "not_implemented",
                    "write_mode": "none",
                    "reason": "no_memoryops_long_term_store",
                },
                "retrieved_knowledge_evidence": {
                    "available": True,
                    "promotion_mode": "explicit_only",
                    "stored_as_memory_by_default": False,
                },
                "conversation_summary": {
                    "available": summary_entry is not None,
                    "source": "conversation_summaries",
                },
            },
            "entries": entries,
        }

    def _instruction_entries(self, agent_memory_contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        entries = agent_memory_contract.get("memory_entries") or []
        if not isinstance(entries, list):
            return []
        return [self._instruction_entry(entry) for entry in entries if isinstance(entry, dict)]

    def _instruction_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        memory_id = str(entry.get("memory_id") or "").strip() or "memory:unknown"
        scope = str(entry.get("scope") or "global").strip() or "global"
        source = str(entry.get("source") or "agent_memory_layer").strip() or "agent_memory_layer"
        confidence = self._coerce_confidence(entry.get("confidence"), default=1.0)
        expires_at = self._serialize_time(entry.get("expires_at"))
        return {
            "contract_version": MEMORYOPS_CONTRACT_VERSION,
            "memory_id": memory_id,
            "kind": MEMORY_KIND_RUNTIME_INSTRUCTION,
            "source": source,
            "scope": scope,
            "status": STATUS_ACTIVE,
            "confidence": confidence,
            "ttl_policy": TTL_NONE if not expires_at else "expires_at",
            "expires_at": expires_at,
            "content_excerpt": self._excerpt(entry.get("content")),
            "retrieval_reason": str(entry.get("retrieval_reason") or "").strip(),
            "injection_trace": {
                "mode": "existing_runtime_path",
                "path": "AgentMemoryService.build_context",
                "behavior_changed": False,
            },
        }

    def _conversation_summary_entry(self, summary: Optional[Any]) -> Optional[Dict[str, Any]]:
        if summary is None:
            return None
        summary_id = getattr(summary, "id", None)
        conversation_id = getattr(summary, "conversation_id", None)
        memory_id = f"conversation_summary:{conversation_id}:{summary_id or 'latest'}"
        return {
            "contract_version": MEMORYOPS_CONTRACT_VERSION,
            "memory_id": memory_id,
            "kind": MEMORY_KIND_CONVERSATION_SUMMARY,
            "source": "conversation_summaries",
            "scope": f"conversation:{conversation_id}",
            "status": STATUS_ACTIVE,
            "confidence": 1.0,
            "ttl_policy": TTL_NONE,
            "expires_at": None,
            "content_excerpt": self._excerpt(getattr(summary, "summary", "")),
            "message_count": int(getattr(summary, "message_count", 0) or 0),
            "last_message_id": getattr(summary, "last_message_id", None),
            "trigger": str(getattr(summary, "trigger", "") or "manual"),
            "created_at": self._serialize_time(getattr(summary, "created_at", None)),
            "audit_source": "messages",
            "injection_trace": {
                "mode": "existing_runtime_path",
                "path": "ChatContextPackingService.pack",
                "behavior_changed": False,
            },
        }

    @staticmethod
    def _coerce_confidence(value: Any, *, default: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, number))

    @staticmethod
    def _serialize_time(value: Any) -> Optional[str]:
        if value is None:
            return None
        try:
            return value.isoformat()
        except AttributeError:
            text = str(value).strip()
            return text or None

    @staticmethod
    def _excerpt(value: Any, *, limit: int = 240) -> str:
        text = " ".join(str(value or "").split())
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."


_memoryops_contract_service: Optional[MemoryOpsContractService] = None


def get_memoryops_contract_service() -> MemoryOpsContractService:
    global _memoryops_contract_service
    if _memoryops_contract_service is None:
        _memoryops_contract_service = MemoryOpsContractService()
    return _memoryops_contract_service
