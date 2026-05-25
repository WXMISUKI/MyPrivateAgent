"""Helpers for orchestrator runtime event post-processing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OrchestratorStreamState:
    """Accumulates stream state while the harness emits runtime events."""

    full_content: str = ""
    last_content_chunk: str = ""
    last_reasoning: str = ""


def persist_tool_artifact(
    *,
    artifact_store: Any,
    conversation_id: int,
    event_data: Dict[str, Any],
    selected_model: str,
) -> None:
    """Persist tool results as schema-aware artifacts for replay and debugging."""
    envelope = event_data.get("tool_execution_envelope")
    if not isinstance(envelope, dict):
        envelope = event_data.get("tool_result_envelope")
    if not isinstance(envelope, dict):
        envelope = {}

    tool_name = str(envelope.get("tool_name") or event_data.get("name", "") or "").strip()
    tool_result = str(envelope.get("result_text") or event_data.get("result", "") or "").strip()

    if not tool_name or not tool_result:
        return

    envelope_card = envelope.get("card") if isinstance(envelope.get("card"), dict) else None
    event_card = event_data.get("card") if isinstance(event_data.get("card"), dict) else None
    card = envelope_card or event_card
    card_schema = envelope.get("card_schema") or event_data.get("card_schema") or (card.get("schema") if card else None)
    artifact_ref = envelope.get("artifact_ref") if isinstance(envelope.get("artifact_ref"), dict) else None
    tool_spec = envelope.get("tool_spec") if isinstance(envelope.get("tool_spec"), dict) else event_data.get("tool_spec")
    metadata = {
        "tool_name": tool_name,
        "tool_call_id": envelope.get("tool_call_id") or event_data.get("tool_call_id"),
        "tool_spec": tool_spec,
        "model_name": selected_model,
    }
    if artifact_ref:
        metadata["artifact_ref"] = artifact_ref
    tool_execution = envelope.get("execution_metadata") if isinstance(envelope.get("execution_metadata"), dict) else None
    if not tool_execution:
        tool_execution = event_data.get("tool_execution") if isinstance(event_data.get("tool_execution"), dict) else None
    if tool_execution:
        metadata["tool_execution"] = tool_execution
        for key in ("cache_hit", "duration_ms", "result_source", "status"):
            if key in tool_execution:
                metadata[key] = tool_execution[key]
    if card:
        metadata["card_kind"] = card.get("kind")
        for key in ("source", "source_label", "source_count"):
            if key in card:
                metadata[key] = card.get(key)

    artifact_store.create_artifact(
        conversation_id=conversation_id,
        kind="tool_result",
        content=tool_result,
        render_mode=envelope.get("render_mode") or event_data.get("render_mode"),
        card_schema=card_schema,
        card=card,
        metadata=metadata,
    )


def persist_runtime_knowledge_artifact(
    *,
    artifact_store: Any,
    conversation_id: int,
    knowledge_context: Any,
    selected_model: str,
) -> None:
    """Persist the runtime knowledge snapshot injected into the current run."""
    if not knowledge_context or not getattr(knowledge_context, "system_prompt", "").strip():
        return

    artifact_store.create_artifact(
        conversation_id=conversation_id,
        kind="runtime_knowledge",
        content=knowledge_context.system_prompt,
        render_mode="plain_text",
        metadata={
            "model_name": selected_model,
            "prompt_keys": list(getattr(knowledge_context, "prompt_keys", []) or []),
            "practice_ids": list(getattr(knowledge_context, "practice_ids", []) or []),
            "prompt_count": getattr(knowledge_context, "prompt_count", 0),
            "practice_count": getattr(knowledge_context, "practice_count", 0),
            **dict(getattr(knowledge_context, "metadata", {}) or {}),
        },
    )


def persist_runtime_knowledge_effect_artifact(
    *,
    artifact_store: Any,
    conversation_id: int,
    knowledge_context: Any,
    selected_model: str,
    stop_reason: Optional[str],
    output_text: str,
) -> None:
    """Persist the run outcome of runtime knowledge usage for later evaluation."""
    if not knowledge_context or not getattr(knowledge_context, "metadata", None):
        return

    metadata = dict(getattr(knowledge_context, "metadata", {}) or {})
    selected_items = list(metadata.get("selected_items", []) or [])
    if not selected_items:
        return

    content = (
        f"scope={metadata.get('scope', 'global')}; "
        f"selected={len(selected_items)}; "
        f"stop_reason={stop_reason or 'completed'}; "
        f"output_length={len(output_text or '')}"
    )
    artifact_store.create_artifact(
        conversation_id=conversation_id,
        kind="runtime_knowledge_effect",
        content=content,
        render_mode="plain_text",
        metadata={
            "model_name": selected_model,
            "stop_reason": stop_reason,
            "output_length": len(output_text or ""),
            "scope": metadata.get("scope"),
            "selected_items": selected_items,
            "selected_count": len(selected_items),
            "prompt_keys": metadata.get("prompt_keys", []),
            "practice_ids": metadata.get("practice_ids", []),
        },
    )


def persist_runtime_skill_artifact(
    *,
    artifact_store: Any,
    conversation_id: int,
    skill_context: Any,
    selected_model: str,
) -> None:
    """Persist the runtime skill snapshot injected into the current run."""
    if not skill_context or not getattr(skill_context, "system_prompt", "").strip():
        return

    artifact_store.create_artifact(
        conversation_id=conversation_id,
        kind="runtime_skill",
        content=skill_context.system_prompt,
        render_mode="plain_text",
        metadata={
            "model_name": selected_model,
            **dict(getattr(skill_context, "metadata", {}) or {}),
        },
    )


def persist_runtime_skill_effect_artifact(
    *,
    artifact_store: Any,
    conversation_id: int,
    skill_context: Any,
    selected_model: str,
    stop_reason: Optional[str],
    output_text: str,
) -> None:
    """Persist the run outcome of runtime skill selection for later review."""
    if not skill_context or not getattr(skill_context, "metadata", None):
        return

    metadata = dict(getattr(skill_context, "metadata", {}) or {})
    selected_items = list(metadata.get("selected_items", []) or [])
    if not selected_items:
        return

    artifact_store.create_artifact(
        conversation_id=conversation_id,
        kind="runtime_skill_effect",
        content=(
            f"selected={len(selected_items)}; "
            f"stop_reason={stop_reason or 'completed'}; "
            f"output_length={len(output_text or '')}"
        ),
        render_mode="plain_text",
        metadata={
            "model_name": selected_model,
            "selected_items": selected_items,
            "selected_count": len(selected_items),
            "selected_skill_ids": metadata.get("selected_skill_ids", []),
            "selected_skill_names": metadata.get("selected_skill_names", []),
            "agent_role": metadata.get("agent_role"),
            "stop_reason": stop_reason,
            "output_length": len(output_text or ""),
        },
    )


def build_done_payload(
    *,
    chunk_data: Dict[str, Any],
    full_answer: str,
    reasoning_content: Optional[str],
    context_stats: Dict[str, Any],
) -> str:
    """Build the final done payload emitted by the orchestrator."""
    done_payload = {
        "type": "done",
        "content": full_answer,
        "reasoning_content": reasoning_content if reasoning_content else None,
        "context_stats": {
            "tokens": context_stats["total_tokens"],
            "messages": context_stats["message_count"],
            "compression_count": context_stats["compression_count"],
        },
    }
    for key in ("render_mode", "card", "card_schema"):
        if chunk_data.get(key) is not None:
            done_payload[key] = chunk_data.get(key)
    for key in ("tool_name", "tool_call_id", "tool_spec", "tool_execution", "cache_hit", "duration_ms", "result_source", "status"):
        if chunk_data.get(key) is not None:
            done_payload[key] = chunk_data.get(key)
    for key in (
        "event_id",
        "run_id",
        "parent_run_id",
        "conversation_id",
        "iteration",
        "source",
        "severity",
        "summary",
        "detail",
        "state",
        "stop_reason",
        "status_kind",
        "approval_request_id",
        "approval_request",
        "error_category",
        "reason_code",
        "requires_approval",
    ):
        if chunk_data.get(key) is not None:
            done_payload[key] = chunk_data.get(key)
    if isinstance(chunk_data.get("payload"), dict):
        done_payload["payload"] = dict(chunk_data["payload"])

    return json.dumps(done_payload) + "\n"


def should_retry_without_tools(error_content: str) -> bool:
    """Return whether the orchestrator should retry without tool binding."""
    normalized = str(error_content or "")
    return "does not support tools" in normalized or "status code: 400" in normalized
