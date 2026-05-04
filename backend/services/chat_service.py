"""Chat route support services for conversation persistence and response assembly."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


def _get_planner_service_cls():
    try:
        from services.planner_service import PlannerService
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.planner_service import PlannerService
    return PlannerService


def _get_mcp_adapter_service():
    try:
        from services.mcp_adapter_service import get_mcp_adapter_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.mcp_adapter_service import get_mcp_adapter_service
    return get_mcp_adapter_service()


def _get_scheduler_service_cls():
    try:
        from services.scheduler_service import SchedulerService
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.scheduler_service import SchedulerService
    return SchedulerService


def _get_orchestrator_factory():
    try:
        from orchestrator import get_orchestrator
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.orchestrator import get_orchestrator
    return get_orchestrator


def _get_policy_engine_service():
    try:
        from services.policy_engine_service import get_policy_engine_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.policy_engine_service import get_policy_engine_service
    return get_policy_engine_service()


def extract_event_field(event: Dict[str, Any], key: str, default: Any = "") -> Any:
    """Read a field from canonical events, supporting both top-level and payload locations."""
    payload = event.get("payload") or {}
    if key in event and event.get(key) is not None:
        return event.get(key)
    if key in payload and payload.get(key) is not None:
        return payload.get(key)
    return default


def _excerpt_text(value: Any, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _infer_error_category_from_text(result_text: str) -> str:
    text = str(result_text or "").lower()
    if "timeout" in text:
        return "provider_timeout"
    if "connection" in text:
        return "provider_connection"
    if "network" in text:
        return "provider_network"
    if "rate limit" in text or "429" in text:
        return "provider_rate_limit"
    if "503" in text or "502" in text or "unavailable" in text:
        return "provider_unavailable"
    if "validation error" in text:
        return "tool_validation"
    return ""


def _build_run_trace_from_runtime_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    event_type = str(event.get("type") or "").strip()
    if not event_type:
        return None
    trace_model_name = str(extract_event_field(event, "model_name", "") or "").strip()
    trace_provider = str(extract_event_field(event, "provider", "") or "").strip()

    if event_type == "state":
        previous_state = str(extract_event_field(event, "previous_state", "") or "").strip()
        state = str(extract_event_field(event, "state", "") or "").strip()
        stop_reason = str(extract_event_field(event, "stop_reason", "") or "").strip()
        return {
            "source": "runtime",
            "event_type": "agent_state_changed",
            "summary": f"Agent 状态迁移到 `{state or 'unknown'}`",
            "detail": f"{previous_state} -> {state}" + (f" | stop_reason={stop_reason}" if stop_reason else ""),
            "severity": "warning" if state in {"failed", "aborted"} else "info",
            "payload": {
                "previous_state": previous_state,
                "state": state,
                "stop_reason": stop_reason,
                "model_name": trace_model_name,
                "provider": trace_provider,
            },
        }

    if event_type == "tool_permission_required":
        tool_name = str(extract_event_field(event, "name", "") or "").strip()
        request_id = str(extract_event_field(event, "request_id", "") or "").strip()
        permission_level = str(extract_event_field(event, "permission_level", "") or "").strip()
        return {
            "source": "permission",
            "event_type": "tool_permission_required",
            "summary": f"工具 `{tool_name or 'unknown'}` 等待授权",
            "detail": f"request_id={request_id}" if request_id else "",
            "severity": "warning",
            "payload": {
                "tool_name": tool_name,
                "request_id": request_id,
                "permission_level": permission_level,
                "tool_args": extract_event_field(event, "args", {}) or {},
            },
        }

    if event_type == "status":
        status_kind = str(extract_event_field(event, "status_kind", "") or "").strip()
        if status_kind == "runtime_skills":
            selected_items = extract_event_field(event, "selected_items", []) or []
            selected_names = [
                str(item.get("name") or "").strip()
                for item in selected_items
                if isinstance(item, dict) and str(item.get("name") or "").strip()
            ]
            selected_count = int(extract_event_field(event, "selected_count", len(selected_names)) or 0)
            agent_role = str(extract_event_field(event, "agent_role", "") or "").strip()
            summary = f"运行时 Skill 已选择 {selected_count} 项"
            if selected_names:
                summary += f": {', '.join(selected_names[:3])}"
            return {
                "source": "skill",
                "event_type": "runtime_skills_selected",
                "summary": summary,
                "detail": f"agent_role={agent_role}" if agent_role else "",
                "severity": "info",
                "payload": {
                    "selected_count": selected_count,
                    "selected_items": selected_items,
                    "agent_role": agent_role,
                },
            }
        if status_kind == "execution_progress":
            phase = str(extract_event_field(event, "phase", "") or "").strip()
            content = str(extract_event_field(event, "content", "") or "").strip()
            completion_check = extract_event_field(event, "completion_check", {}) or {}
            profile = str(completion_check.get("profile") or "").strip()
            completion_stage = str(completion_check.get("stage") or phase or "").strip()
            if phase == "completion_retry":
                missing_parts = completion_check.get("missing_parts") or []
                return {
                    "source": "agent",
                    "event_type": "completion_retry",
                    "summary": "框架已触发一次受控补查",
                    "detail": content,
                    "severity": "info",
                    "payload": {
                        "phase": phase,
                        "profile": profile,
                        "completion_stage": completion_stage,
                        "missing_parts": missing_parts,
                        "completion_check": completion_check,
                    },
                }
            if phase == "boundary_fallback":
                missing_parts = completion_check.get("missing_parts") or []
                missing_text = ", ".join(str(item) for item in missing_parts)
                hook_fallback = completion_check.get("hook_fallback") or {}
                return {
                    "source": "agent",
                    "event_type": "capability_gap_fallback",
                    "summary": "框架已触发能力边界降级收口",
                    "detail": content,
                    "severity": "warning",
                    "payload": {
                        "phase": phase,
                        "profile": profile,
                        "completion_stage": completion_stage,
                        "missing_parts": missing_parts,
                        "missing_text": missing_text,
                        "completion_check": completion_check,
                        "hook_fallback": hook_fallback,
                        "model_name": trace_model_name,
                        "provider": trace_provider,
                    },
                }

    if event_type == "tool_denied":
        tool_name = str(extract_event_field(event, "name", "") or "").strip()
        reason = str(extract_event_field(event, "reason", "") or "").strip()
        hook_decision = extract_event_field(event, "hook_decision", {}) or {}
        if "治理策略阻断" in reason:
            return {
                "source": "hook",
                "event_type": "pre_tool_use_blocked",
                "summary": f"Hook 已阻断工具 `{tool_name or 'unknown'}` 自动执行",
                "detail": reason,
                "severity": "warning",
                "payload": {
                    "tool_name": tool_name,
                    "reason": reason,
                    "hook_decision": hook_decision,
                    "model_name": trace_model_name,
                    "provider": trace_provider,
                },
            }
        return {
            "source": "permission",
            "event_type": "tool_denied",
            "summary": f"工具 `{tool_name or 'unknown'}` 被拒绝执行",
            "detail": reason,
            "severity": "warning",
            "payload": {
                "tool_name": tool_name,
                "reason": reason,
                "model_name": trace_model_name,
                "provider": trace_provider,
            },
        }

    if event_type != "tool_result":
        if event_type == "content":
            completion_check = extract_event_field(event, "completion_check", {}) or {}
            if completion_check:
                return {
                    "source": "agent",
                    "event_type": "completion_finalized",
                    "summary": "框架已基于完成度评估生成最终收尾",
                    "detail": _excerpt_text(extract_event_field(event, "content", "")),
                    "severity": "info",
                    "payload": {
                        "profile": str(completion_check.get("profile") or "").strip(),
                        "completion_stage": str(completion_check.get("stage") or "finalized").strip(),
                        "completion_check": completion_check,
                        "framework_notice": bool(extract_event_field(event, "framework_notice", False)),
                        "model_name": trace_model_name,
                        "provider": trace_provider,
                    },
                }
        return None

    tool_name = str(extract_event_field(event, "name", "") or "").strip()
    tool_execution = extract_event_field(event, "tool_execution", {}) or {}
    status = str(extract_event_field(event, "status", tool_execution.get("status", "")) or "").strip()
    result_source = str(extract_event_field(event, "result_source", tool_execution.get("result_source", "")) or "").strip()
    duration_ms = extract_event_field(event, "duration_ms", tool_execution.get("duration_ms"))
    cache_hit = extract_event_field(event, "cache_hit", tool_execution.get("cache_hit"))
    error_category = str(
        extract_event_field(event, "error_category", tool_execution.get("error_category", "")) or ""
    ).strip()
    result_text = str(extract_event_field(event, "result", "") or "").strip()
    tool_call_id = str(extract_event_field(event, "tool_call_id", "") or "").strip()
    is_mcp_tool = tool_name.startswith("mcp_")
    hook_post = tool_execution.get("hook_post") if isinstance(tool_execution, dict) else None

    if status == "pending_permission":
        return None

    if status == "error" or result_text.startswith("执行错误:"):
        summary = f"{'MCP 能力' if is_mcp_tool else '工具'} `{tool_name or 'unknown'}` 执行失败"
        severity = "error"
        trace_event_type = "mcp_tool_failed" if is_mcp_tool else "tool_failed"
        if not error_category:
            error_category = _infer_error_category_from_text(result_text)
    else:
        summary = f"{'MCP 能力' if is_mcp_tool else '工具'} `{tool_name or 'unknown'}` 执行完成"
        severity = "success" if status in {"ok", "cached"} else "info"
        trace_event_type = "mcp_tool_called" if is_mcp_tool else "tool_called"

    return {
        "source": "mcp" if is_mcp_tool else "tool",
        "event_type": trace_event_type,
        "summary": summary,
        "detail": _excerpt_text(result_text),
        "severity": severity,
        "payload": {
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "status": status,
            "result_source": result_source,
            "duration_ms": duration_ms,
            "cache_hit": cache_hit,
            "error_category": error_category,
            "hook_post": hook_post or {},
            "model_name": trace_model_name,
            "provider": trace_provider,
        },
    }


def maybe_append_runtime_run_trace(
    *,
    db: Optional[Session],
    user_id: Optional[int],
    conversation_id: Optional[int],
    execution_context: Optional[Dict[str, Any]],
    event: Dict[str, Any],
) -> None:
    if db is None or user_id is None or conversation_id is None or not execution_context:
        return

    plan_item_id = execution_context.get("plan_item_id")
    if plan_item_id is None:
        return

    trace_event = _build_run_trace_from_runtime_event(event)
    if trace_event is None:
        return

    try:
        planner_service = _get_planner_service_cls()(db)
        plan = planner_service.get_latest_plan_for_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if plan is None:
            return
        _get_scheduler_service_cls()(db).append_run_trace_event(
            plan=plan,
            item_id=plan_item_id,
            source=trace_event["source"],
            event_type=trace_event["event_type"],
            summary=trace_event["summary"],
            detail=trace_event["detail"],
            severity=trace_event["severity"],
            payload=trace_event["payload"],
        )
    except Exception as exc:  # pragma: no cover - defensive runtime logging
        logger.warning(f"[Chat] 追加运行 Trace 失败: {exc}")


def get_or_create_conversation(
    *,
    request: Any,
    current_user: Any,
    db: Session,
) -> tuple[Any, list[Any]]:
    """Load an existing conversation or create a new one for the current request."""
    try:
        from models import Conversation, Message
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.models import Conversation, Message

    conversation = None

    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()

    if not conversation:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:30] + ("..." if len(request.message) > 30 else ""),
            model_name=request.model_name or "doubao",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    history_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    if request.model_name and request.model_name != conversation.model_name:
        conversation.model_name = request.model_name

    conversation.updated_at = datetime.now()
    if len(history_messages) == 0:
        conversation.title = request.message[:20] + ("..." if len(request.message) > 20 else "")

    db.add(Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    ))
    db.commit()

    return conversation, history_messages


def save_assistant_message(db: Session, conversation_id: int, content: str) -> Optional[Any]:
    """Persist the assistant response if non-empty and return the saved message."""
    if not content:
        return None

    try:
        from models import Message
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.models import Message

    message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def record_learning_if_possible(
    *,
    db: Session,
    user_message: str,
    assistant_content: str,
    user_id: Optional[int],
) -> None:
    """Best-effort learning capture for completed conversations."""
    if not assistant_content:
        return

    try:
        try:
            from learning_recorder import LearningRecorder
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.learning_recorder import LearningRecorder

        recorder = LearningRecorder()
        conversation_text = f"用户: {user_message}\n助手: {assistant_content}"
        records = recorder.record_from_conversation(
            conversation_text=conversation_text,
            db=db,
            user_id=user_id,
            area=None,
        )
        if records:
            logger.info(f"[Chat] 自学习：记录了 {len(records)} 条学习内容")
    except Exception as e:  # pragma: no cover - defensive runtime logging
        logger.error(f"[Chat] 自学习记录失败: {e}")


def maybe_start_plan_for_chat(
    *,
    db: Session,
    user_id: int,
    conversation_id: int,
) -> Optional[Dict[str, Any]]:
    """Prepare planner execution and optional pseudo-subagent handoff before chat execution."""
    try:
        service = _get_planner_service_cls()(db)
        plan = service.get_latest_plan_for_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if plan is None:
            return None

        updated = service.begin_execution(plan=plan)
        if updated is None:
            return None

        events: List[Dict[str, Any]] = [{
            "type": "plan_updated",
            "conversation_id": conversation_id,
            "plan": service.serialize_plan(updated),
        }]

        active_item = service.get_active_item(plan=updated)
        execution_context = None

        if active_item:
            required_capabilities = list((active_item.item_metadata or {}).get("required_capabilities", []))
            if required_capabilities:
                capability_state = _get_mcp_adapter_service().validate_capabilities(required_capabilities)
                if not capability_state["ready"]:
                    missing_capabilities = capability_state["missing_capabilities"]
                    unavailable_capabilities = capability_state["unavailable_capabilities"]
                    blocked_message = _build_capability_blocked_message(
                        plan_item_title=active_item.title,
                        missing_capabilities=missing_capabilities,
                        unavailable_capabilities=unavailable_capabilities,
                    )
                    blocked_plan = service.block_active_item(
                        plan=updated,
                        reason=blocked_message,
                        missing_capabilities=missing_capabilities,
                        unavailable_capabilities=unavailable_capabilities,
                    )
                    _get_scheduler_service_cls()(db).append_run_trace_event(
                        plan=blocked_plan or updated,
                        item_id=active_item.id,
                        source="capability",
                        event_type="capability_blocked",
                        summary="计划项因能力依赖不满足被阻塞",
                        detail=blocked_message,
                        severity="error",
                        payload={
                            "missing_capabilities": missing_capabilities,
                            "unavailable_capabilities": unavailable_capabilities,
                        },
                    )
                    events.append({
                        "type": "plan_updated",
                        "conversation_id": conversation_id,
                        "plan": service.serialize_plan(blocked_plan or updated),
                    })
                    events.append({
                        "type": "status",
                        "status_kind": "capability_blocked",
                        "conversation_id": conversation_id,
                        "content": blocked_message,
                        "plan_id": getattr(blocked_plan or updated, "id", None),
                        "plan_item_id": active_item.id,
                        "plan_item_title": active_item.title,
                        "missing_capabilities": missing_capabilities,
                        "unavailable_capabilities": unavailable_capabilities,
                    })
                    return {
                        "events": events,
                        "execution_context": None,
                        "blocked": True,
                        "blocked_message": blocked_message,
                    }

        scheduler_state = _get_scheduler_service_cls()(db).prepare_execution(plan=updated, item=active_item) if active_item else None

        if scheduler_state:
            scheduled_plan = scheduler_state["plan"]
            events.append({
                "type": "plan_updated",
                "conversation_id": conversation_id,
                "plan": service.serialize_plan(scheduled_plan),
            })
            events.append({
                "type": "status",
                "status_kind": "scheduler_fanout_prepared",
                "conversation_id": conversation_id,
                "content": f"当前步骤已拆分为 {scheduler_state['child_count']} 个子智能体执行单元",
                "plan_id": scheduled_plan.id,
                "plan_item_id": active_item.id,
                "plan_item_title": active_item.title,
                "agent_id": active_item.agent_id,
                "child_roles": scheduler_state["child_roles"],
                "child_count": scheduler_state["child_count"],
            })
            execution_context = scheduler_state["execution_context"]
        elif active_item and active_item.agent_role and active_item.agent_role != "general":
            handed_off_plan = service.prepare_handoff(plan=updated)
            active_item = service.get_active_item(plan=handed_off_plan)
            if handed_off_plan is not None and active_item is not None:
                events.append({
                    "type": "plan_updated",
                    "conversation_id": conversation_id,
                    "plan": service.serialize_plan(handed_off_plan),
                })
                events.append({
                    "type": "status",
                    "status_kind": "agent_handoff",
                    "conversation_id": conversation_id,
                    "content": f"已将当前步骤交给 {active_item.agent_role} 子智能体执行",
                    "agent_role": active_item.agent_role,
                    "agent_id": active_item.agent_id,
                    "plan_id": handed_off_plan.id,
                    "plan_item_id": active_item.id,
                    "plan_item_title": active_item.title,
                })

                execution_context = {
                    "plan_id": handed_off_plan.id,
                    "plan_item_id": active_item.id,
                    "plan_item_title": active_item.title,
                    "agent_role": active_item.agent_role,
                    "agent_id": active_item.agent_id,
                    "required_capabilities": list((active_item.item_metadata or {}).get("required_capabilities", [])),
                    "handoff_status": (
                        active_item.handoff_status.value
                        if hasattr(active_item.handoff_status, "value")
                        else str(active_item.handoff_status)
                    ),
                }

        return {
            "events": events,
            "execution_context": execution_context,
        }
    except Exception as e:  # pragma: no cover - defensive runtime logging
        logger.error(f"[Chat] 启动计划执行状态失败: {e}")
        return None


def maybe_mark_plan_handoff_executing(
    *,
    db: Session,
    user_id: int,
    conversation_id: int,
) -> Optional[Dict[str, Any]]:
    """Promote the active pseudo-subagent handoff from handed_off to executing."""
    try:
        service = _get_planner_service_cls()(db)
        plan = service.get_latest_plan_for_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if plan is None:
            return None

        scheduler_service = _get_scheduler_service_cls()(db)
        active_item = service.get_active_item(plan=plan)
        if active_item is None:
            return None

        scheduler_state = scheduler_service.prepare_execution(plan=plan, item=active_item)
        if scheduler_state:
            updated = scheduler_service.mark_execution_started(plan=plan, item_id=active_item.id)
        else:
            if not active_item.agent_role or active_item.agent_role == "general":
                return None
            updated = service.mark_handoff_executing(plan=plan)
        if updated is None:
            return None

        executing_item = service.get_active_item(plan=updated)
        if executing_item is None:
            return None

        scheduler_group = ((executing_item.item_metadata or {}).get("child_execution_group") or {})
        child_contexts = [
            {
                "plan_id": updated.id,
                "plan_item_id": executing_item.id,
                "plan_item_title": executing_item.title,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "required_capabilities": list((executing_item.item_metadata or {}).get("required_capabilities", [])),
                "handoff_status": "executing",
                "child_execution_id": child.get("child_execution_id"),
                "scheduler_run_id": scheduler_group.get("run_id"),
            }
            for child in (scheduler_group.get("children") or [])
        ]
        if len(child_contexts) > 1:
            return {
                "events": [
                    {
                        "type": "plan_updated",
                        "conversation_id": conversation_id,
                        "plan": service.serialize_plan(updated),
                    },
                    {
                        "type": "status",
                        "status_kind": "scheduler_execution",
                        "conversation_id": conversation_id,
                        "content": f"已启动 {len(child_contexts)} 个子智能体执行单元",
                        "plan_id": updated.id,
                        "plan_item_id": executing_item.id,
                        "plan_item_title": executing_item.title,
                        "agent_id": executing_item.agent_id,
                        "child_count": len(child_contexts),
                    },
                ],
                "execution_context": {
                    "scheduler_mode": "fan_out",
                    "scheduler_run_id": scheduler_group.get("run_id"),
                    "merge_strategy": scheduler_group.get("merge_strategy"),
                    "plan_id": updated.id,
                    "plan_item_id": executing_item.id,
                    "plan_item_title": executing_item.title,
                    "agent_role": str(executing_item.agent_role or "scheduler").strip() or "scheduler",
                    "agent_id": executing_item.agent_id,
                    "required_capabilities": list((executing_item.item_metadata or {}).get("required_capabilities", [])),
                    "handoff_status": (
                        executing_item.handoff_status.value
                        if hasattr(executing_item.handoff_status, "value")
                        else str(executing_item.handoff_status)
                    ),
                    "child_contexts": child_contexts,
                },
            }

        return {
            "events": [
                {
                    "type": "plan_updated",
                    "conversation_id": conversation_id,
                    "plan": service.serialize_plan(updated),
                },
                {
                    "type": "status",
                    "status_kind": "agent_execution",
                    "conversation_id": conversation_id,
                    "content": f"{executing_item.agent_role} 子智能体开始执行当前步骤",
                    "agent_role": executing_item.agent_role,
                    "agent_id": executing_item.agent_id,
                    "plan_id": updated.id,
                    "plan_item_id": executing_item.id,
                    "plan_item_title": executing_item.title,
                },
            ],
            "execution_context": {
                "plan_id": updated.id,
                "plan_item_id": executing_item.id,
                "plan_item_title": executing_item.title,
                "agent_role": executing_item.agent_role,
                "agent_id": executing_item.agent_id,
                "required_capabilities": list((executing_item.item_metadata or {}).get("required_capabilities", [])),
                "handoff_status": (
                    executing_item.handoff_status.value
                    if hasattr(executing_item.handoff_status, "value")
                    else str(executing_item.handoff_status)
                ),
            },
        }
    except Exception as e:  # pragma: no cover - defensive runtime logging
        logger.error(f"[Chat] 推进计划交接执行状态失败: {e}")
        return None


def maybe_complete_plan_after_chat(
    *,
    db: Session,
    user_id: int,
    conversation_id: int,
    assistant_content: str,
) -> Optional[Dict[str, Any]]:
    """Complete the active plan item after a successful assistant response."""
    if not assistant_content.strip():
        return None

    try:
        service = _get_planner_service_cls()(db)
        plan = service.get_latest_plan_for_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if plan is None:
            return None

        updated = service.complete_execution(
            plan=plan,
            note=assistant_content[:200],
        )
        if updated is None:
            return None

        return {
            "type": "plan_updated",
            "conversation_id": conversation_id,
            "plan": service.serialize_plan(updated),
        }
    except Exception as e:  # pragma: no cover - defensive runtime logging
        logger.error(f"[Chat] 完成计划执行状态失败: {e}")
        return None


def _build_capability_blocked_message(
    *,
    plan_item_title: str,
    missing_capabilities: List[str],
    unavailable_capabilities: List[str],
) -> str:
    parts = [f"当前计划项“{plan_item_title}”所需的 MCP capability 不满足，已阻塞执行。"]
    if missing_capabilities:
        parts.append(f"未配置能力：{', '.join(missing_capabilities)}。")
    if unavailable_capabilities:
        parts.append(f"已配置但当前不可用：{', '.join(unavailable_capabilities)}。")
    return "".join(parts)


async def collect_orchestrator_response(
    *,
    orchestrator: Any,
    user_message: str,
    model_name: str,
    execution_context: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> str:
    """Collect the final assistant response from the shared orchestrator path."""
    full_content = ""

    async for chunk in orchestrator.process_message(
        user_message=user_message,
        selected_model=model_name,
        execution_context=execution_context,
    ):
        try:
            parsed = json.loads(chunk)
            if isinstance(parsed, dict):
                maybe_append_runtime_run_trace(
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    execution_context=execution_context,
                    event=parsed,
                )
        except (json.JSONDecodeError, TypeError):
            continue

        event_type = parsed.get("type", "")
        if event_type in ("content", "answer"):
            full_content += extract_event_field(parsed, "content", "") or extract_event_field(parsed, "answer", "")
        elif event_type == "done":
            return extract_event_field(parsed, "content", "") or full_content

    return full_content


async def stream_orchestrator_events(
    *,
    orchestrator: Any,
    user_message: str,
    model_name: str,
    execution_context: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> AsyncGenerator[tuple[str, str], None]:
    """Yield orchestrator chunks together with the accumulated assistant content."""
    actual_content = ""

    async for chunk in orchestrator.process_message(
        user_message=user_message,
        selected_model=model_name,
        execution_context=execution_context,
    ):
        try:
            parsed = json.loads(chunk)
            if isinstance(parsed, dict):
                maybe_append_runtime_run_trace(
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    execution_context=execution_context,
                    event=parsed,
                )
            msg_type = parsed.get("type", "")
            if msg_type in ("content", "answer"):
                actual_content += extract_event_field(parsed, "content", "") or extract_event_field(parsed, "answer", "")
            elif msg_type == "done":
                done_content = extract_event_field(parsed, "content", "") or ""
                if done_content and len(done_content) >= len(actual_content):
                    actual_content = done_content
        except (json.JSONDecodeError, TypeError):
            if chunk.strip():
                actual_content += chunk

        yield chunk, actual_content


async def collect_scheduled_orchestrator_response(
    *,
    orchestrator: Any,
    db: Session,
    user_id: int,
    conversation_id: int,
    user_message: str,
    model_name: str,
    execution_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Execute a fan-out schedule and return the merged result."""
    merged_output = ""
    async for _chunk, actual_content in stream_scheduled_orchestrator_events(
        orchestrator=orchestrator,
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        user_message=user_message,
        model_name=model_name,
        execution_context=execution_context,
    ):
        merged_output = actual_content
    return merged_output


async def stream_scheduled_orchestrator_events(
    *,
    orchestrator: Any,
    db: Session,
    user_id: int,
    conversation_id: int,
    user_message: str,
    model_name: str,
    execution_context: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[tuple[str, str], None]:
    """Execute child contexts sequentially and merge their outputs into one final answer."""
    if not execution_context or execution_context.get("scheduler_mode") != "fan_out":
        async for chunk, actual_content in stream_orchestrator_events(
            orchestrator=orchestrator,
            user_message=user_message,
            model_name=model_name,
            execution_context=execution_context,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        ):
            yield chunk, actual_content
        return

    try:
        from services.subagent_service import get_subagent_runtime_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.subagent_service import get_subagent_runtime_service

    planner_service = _get_planner_service_cls()(db)
    scheduler_service = _get_scheduler_service_cls()(db)
    subagent_runtime_service = get_subagent_runtime_service()
    policy_engine = _get_policy_engine_service()
    orchestrator_factory = _get_orchestrator_factory()
    model_catalog = []
    try:
        model_catalog = list((orchestrator.model_provider.list_available_models() or {}).values())
    except Exception:
        model_catalog = []
    plan = planner_service.get_latest_plan_for_conversation(user_id=user_id, conversation_id=conversation_id)
    actual_content = ""
    show_reasoning = bool(getattr(orchestrator, "show_reasoning", False))
    active_item = planner_service.get_active_item(plan=plan)
    scheduler_policy = scheduler_service.get_execution_policy(active_item)

    yield json.dumps({
        "type": "status",
        "status_kind": "scheduler_fanout_started",
        "conversation_id": conversation_id,
        "content": f"开始并发执行 {len(execution_context.get('child_contexts') or [])} 个子智能体任务",
        "plan_id": execution_context.get("plan_id"),
        "plan_item_id": execution_context.get("plan_item_id"),
        "scheduler_run_id": execution_context.get("scheduler_run_id"),
        "scheduler_policy": scheduler_policy,
    }, ensure_ascii=False), actual_content

    child_tasks = []
    for child_payload in execution_context.get("child_contexts") or []:
        child_context = subagent_runtime_service.normalize_context(child_payload)
        if child_context is None:
            continue
        provider_hint = policy_engine.select_provider_hint(
            requested_model=model_name,
            context={"agent_role": child_context.agent_role},
        )
        model_route = policy_engine.select_model_for_provider(
            requested_model=model_name,
            selected_provider=str(provider_hint.get("selected_provider") or ""),
            available_models=model_catalog,
        )
        child_payload["model_name"] = model_route.get("resolved_model") or model_name
        child_payload["provider_name"] = model_route.get("resolved_provider") or provider_hint.get("selected_provider")
        child_payload["provider_hint"] = provider_hint
        child_payload["provider_order"] = list(provider_hint.get("provider_order") or [])
        scheduler_service.mark_child_policy_selected(
            plan=plan,
            item_id=execution_context.get("plan_item_id"),
            child_execution_id=child_payload.get("child_execution_id"),
            model_name=str(child_payload.get("model_name") or model_name),
            provider_name=str(child_payload.get("provider_name") or ""),
            provider_order=list(child_payload.get("provider_order") or []),
        )

        scheduler_service.mark_child_running(
            plan=plan,
            item_id=execution_context.get("plan_item_id"),
            child_execution_id=child_payload.get("child_execution_id"),
        )
        if plan is not None:
            yield json.dumps({
                "type": "plan_updated",
                "conversation_id": conversation_id,
                "plan": planner_service.serialize_plan(plan),
            }, ensure_ascii=False), actual_content
        yield json.dumps(
            subagent_runtime_service.build_spawn_event(child_context),
            ensure_ascii=False,
        ), actual_content
        scheduler_service.append_run_trace_event(
            plan=plan,
            item_id=execution_context.get("plan_item_id"),
            source="policy",
            event_type="subagent_policy_selected",
            summary=f"{child_context.agent_role} 子智能体策略已加载",
            detail=(
                f"provider={child_payload.get('provider_name')}, "
                f"model={child_payload.get('model_name')}, "
                f"reason={model_route.get('reason')}"
            ),
            severity="info",
            payload={
                "agent_role": child_context.agent_role,
                "agent_id": child_context.agent_id,
                "provider_hint": provider_hint,
                "model_route": model_route,
            },
        )
        if plan is not None:
            yield json.dumps({
                "type": "plan_updated",
                "conversation_id": conversation_id,
                "plan": planner_service.serialize_plan(plan),
            }, ensure_ascii=False), actual_content
        yield json.dumps({
            "type": "status",
            "status_kind": "subagent_policy_selected",
            "conversation_id": conversation_id,
            "agent_role": child_context.agent_role,
            "agent_id": child_context.agent_id,
            "model_name": child_payload.get("model_name"),
            "provider_name": child_payload.get("provider_name"),
            "content": (
                f"{child_context.agent_role} 子智能体将优先使用 "
                f"{child_payload.get('provider_name')} provider / {child_payload.get('model_name')} model"
            ),
            "provider_hint": provider_hint,
            "model_route": model_route,
        }, ensure_ascii=False), actual_content
        child_tasks.append(
            asyncio.create_task(
                _run_parallel_child_execution(
                    orchestrator_factory=orchestrator_factory,
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    show_reasoning=show_reasoning,
                    user_message=user_message,
                    model_name=str(child_payload.get("model_name") or model_name),
                    child_payload=child_payload,
                    child_context=child_context,
                    scheduler_policy=scheduler_policy,
                    policy_engine=policy_engine,
                    model_catalog=model_catalog,
                )
            )
        )

    pending_tasks = set(child_tasks)
    try:
        for completed_task in asyncio.as_completed(child_tasks):
            child_payload, child_context, child_output, outcome = await completed_task
            pending_tasks.discard(completed_task)
            retry_count = outcome.get("retry_count", 0)
            provider_switch_count = int(outcome.get("provider_switch_count", 0) or 0)
            provider_history = list(outcome.get("provider_history") or [])
            scheduler_service.mark_child_policy_selected(
                plan=plan,
                item_id=execution_context.get("plan_item_id"),
                child_execution_id=child_payload.get("child_execution_id"),
                model_name=str(child_payload.get("model_name") or model_name),
                provider_name=str(child_payload.get("provider_name") or ""),
                provider_order=list(child_payload.get("provider_order") or []),
                provider_switch_count=provider_switch_count,
                provider_history=provider_history,
            )
            if provider_switch_count > 0:
                if plan is not None:
                    yield json.dumps({
                        "type": "plan_updated",
                        "conversation_id": conversation_id,
                        "plan": planner_service.serialize_plan(plan),
                    }, ensure_ascii=False), actual_content
                yield json.dumps({
                    "type": "status",
                    "status_kind": "subagent_provider_switched",
                    "conversation_id": conversation_id,
                    "agent_role": child_context.agent_role,
                    "agent_id": child_context.agent_id,
                    "provider_name": child_payload.get("provider_name"),
                    "model_name": child_payload.get("model_name"),
                    "provider_switch_count": provider_switch_count,
                    "provider_history": provider_history,
                    "content": (
                        f"{child_context.agent_role} 子智能体已切换 provider {provider_switch_count} 次，"
                        f"当前使用 {child_payload.get('provider_name')} / {child_payload.get('model_name')}"
                    ),
                }, ensure_ascii=False), actual_content
            if retry_count > 0:
                scheduler_service.mark_child_retrying(
                    plan=plan,
                    item_id=execution_context.get("plan_item_id"),
                    child_execution_id=child_payload.get("child_execution_id"),
                    retry_count=retry_count,
                    error_text=outcome.get("last_error") or "子执行发生重试",
                )
                if plan is not None:
                    yield json.dumps({
                        "type": "plan_updated",
                        "conversation_id": conversation_id,
                        "plan": planner_service.serialize_plan(plan),
                    }, ensure_ascii=False), actual_content
                yield json.dumps({
                    "type": "status",
                    "status_kind": "scheduler_retry",
                    "conversation_id": conversation_id,
                    "content": f"{child_context.agent_role} 子智能体已重试 {retry_count} 次",
                    "agent_role": child_context.agent_role,
                    "agent_id": child_context.agent_id,
                    "plan_id": child_context.plan_id,
                    "plan_item_id": child_context.plan_item_id,
                    "plan_item_title": child_context.plan_item_title,
                    "retry_count": retry_count,
                    "last_error": outcome.get("last_error"),
                }, ensure_ascii=False), actual_content

            if outcome["status"] == "cancelled":
                scheduler_service.mark_child_cancelled(
                    plan=plan,
                    item_id=execution_context.get("plan_item_id"),
                    child_execution_id=child_payload.get("child_execution_id"),
                    reason=outcome.get("error") or "已取消执行",
                )
                if plan is not None:
                    yield json.dumps({
                        "type": "plan_updated",
                        "conversation_id": conversation_id,
                        "plan": planner_service.serialize_plan(plan),
                    }, ensure_ascii=False), actual_content
                yield json.dumps({
                    "type": "status",
                    "status_kind": "subagent_cancelled",
                    "conversation_id": conversation_id,
                    "content": f"{child_context.agent_role} 子智能体已取消",
                    "agent_role": child_context.agent_role,
                    "agent_id": child_context.agent_id,
                    "plan_id": child_context.plan_id,
                    "plan_item_id": child_context.plan_item_id,
                    "plan_item_title": child_context.plan_item_title,
                    "error": outcome.get("error"),
                }, ensure_ascii=False), actual_content
                continue

            if outcome["status"] == "failed":
                scheduler_service.mark_child_failed(
                    plan=plan,
                    item_id=execution_context.get("plan_item_id"),
                    child_execution_id=child_payload.get("child_execution_id"),
                    error_text=outcome.get("error") or "执行失败",
                    error_kind=outcome.get("error_kind") or "failed",
                    retry_count=retry_count,
                )
                if plan is not None:
                    yield json.dumps({
                        "type": "plan_updated",
                        "conversation_id": conversation_id,
                        "plan": planner_service.serialize_plan(plan),
                    }, ensure_ascii=False), actual_content
                yield json.dumps({
                    "type": "status",
                    "status_kind": "subagent_failed",
                    "conversation_id": conversation_id,
                    "content": f"{child_context.agent_role} 子智能体执行失败",
                    "agent_role": child_context.agent_role,
                    "agent_id": child_context.agent_id,
                    "plan_id": child_context.plan_id,
                    "plan_item_id": child_context.plan_item_id,
                    "plan_item_title": child_context.plan_item_title,
                    "error": outcome.get("error"),
                    "error_kind": outcome.get("error_kind"),
                }, ensure_ascii=False), actual_content

                if scheduler_policy.get("cancel_on_failure") and pending_tasks:
                    scheduler_service.append_audit_event(
                        plan=plan,
                        item_id=execution_context.get("plan_item_id"),
                        event_type="scheduler_cancelled",
                        content="检测到子执行失败，已取消剩余子执行任务",
                        payload={
                            "scheduler_run_id": execution_context.get("scheduler_run_id"),
                            "pending_task_count": len(pending_tasks),
                        },
                        commit=False,
                    )
                    scheduler_service.append_run_trace_event(
                        plan=plan,
                        item_id=execution_context.get("plan_item_id"),
                        source="scheduler",
                        event_type="scheduler_cancelled",
                        summary="调度器已取消剩余子执行任务",
                        detail="检测到子执行失败，按策略取消剩余任务。",
                        severity="warning",
                        payload={
                            "scheduler_run_id": execution_context.get("scheduler_run_id"),
                            "pending_task_count": len(pending_tasks),
                        },
                        commit=False,
                    )
                    for pending_task in list(pending_tasks):
                        pending_task.cancel()
                    yield json.dumps({
                        "type": "status",
                        "status_kind": "scheduler_cancelled",
                        "conversation_id": conversation_id,
                        "content": "检测到子执行失败，已取消剩余子智能体任务",
                        "plan_id": execution_context.get("plan_id"),
                        "plan_item_id": execution_context.get("plan_item_id"),
                        "scheduler_run_id": execution_context.get("scheduler_run_id"),
                    }, ensure_ascii=False), actual_content
                continue

            scheduler_service.mark_child_completed(
                plan=plan,
                item_id=execution_context.get("plan_item_id"),
                child_execution_id=child_payload.get("child_execution_id"),
                output_text=child_output,
            )
            if plan is not None:
                yield json.dumps({
                    "type": "plan_updated",
                    "conversation_id": conversation_id,
                    "plan": planner_service.serialize_plan(plan),
                }, ensure_ascii=False), actual_content
            yield json.dumps(
                subagent_runtime_service.build_collect_event(
                    child_context,
                    output_text=child_output,
                ),
                ensure_ascii=False,
            ), actual_content
    finally:
        for pending_task in pending_tasks:
            pending_task.cancel()
        if pending_tasks:
            await asyncio.gather(*pending_tasks, return_exceptions=True)

    merge_state = scheduler_service.merge_child_outputs(
        plan=plan,
        item_id=execution_context.get("plan_item_id"),
    )
    actual_content = merge_state.get("merged_output") or ""
    if plan is not None:
        yield json.dumps({
            "type": "plan_updated",
            "conversation_id": conversation_id,
            "plan": planner_service.serialize_plan(plan),
        }, ensure_ascii=False), actual_content
    yield json.dumps({
        "type": "status",
        "status_kind": "scheduler_merged",
        "conversation_id": conversation_id,
        "content": "已完成多子智能体结果合并",
        "plan_id": execution_context.get("plan_id"),
        "plan_item_id": execution_context.get("plan_item_id"),
        "scheduler_run_id": execution_context.get("scheduler_run_id"),
        "merge_status": merge_state.get("merge_status"),
        "completed_children": merge_state.get("completed_children"),
        "failed_children": merge_state.get("failed_children"),
    }, ensure_ascii=False), actual_content
    if actual_content:
        yield json.dumps({"type": "content", "content": actual_content}, ensure_ascii=False), actual_content
    yield json.dumps({"type": "done", "content": actual_content}, ensure_ascii=False), actual_content


async def _run_parallel_child_execution(
    *,
    orchestrator_factory: Any,
    db: Optional[Session],
    user_id: Optional[int],
    conversation_id: int,
    show_reasoning: bool,
    user_message: str,
    model_name: str,
    child_payload: Dict[str, Any],
    child_context: Any,
    scheduler_policy: Dict[str, Any],
    policy_engine: Any,
    model_catalog: List[Dict[str, Any]],
) -> tuple[Dict[str, Any], Any, str, Dict[str, Any]]:
    child_orchestrator = orchestrator_factory(
        conversation_id=conversation_id,
        show_reasoning=show_reasoning,
    )
    max_retries = max(0, int(scheduler_policy.get("max_retries", 0)))
    timeout_seconds = max(1, int(scheduler_policy.get("timeout_seconds", 45)))
    attempt = 0
    last_error = ""
    last_error_kind = "failed"
    provider_order = list(child_payload.get("provider_order") or [])
    provider_pointer = 0
    if not provider_order and child_payload.get("provider_name"):
        provider_order = [str(child_payload.get("provider_name"))]
    provider_history: List[Dict[str, Any]] = [{
        "provider_name": str(child_payload.get("provider_name") or ""),
        "model_name": str(child_payload.get("model_name") or model_name),
        "reason": "initial",
    }]

    while attempt <= max_retries:
        attempt += 1
        current_model_name = str(child_payload.get("model_name") or model_name)
        try:
            output_text = await asyncio.wait_for(
                collect_orchestrator_response(
                    orchestrator=child_orchestrator,
                    user_message=user_message,
                    model_name=current_model_name,
                    execution_context=child_payload,
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                ),
                timeout=timeout_seconds,
            )
            return child_payload, child_context, output_text, {
                "status": "completed",
                "retry_count": max(0, attempt - 1),
                "last_error": last_error,
                "error_kind": None,
                "provider_switch_count": max(0, provider_pointer),
                "provider_history": provider_history,
            }
        except asyncio.CancelledError:
            return child_payload, child_context, "", {
                "status": "cancelled",
                "retry_count": max(0, attempt - 1),
                "last_error": last_error,
                "error": "调度器已取消该子执行",
                "error_kind": "cancelled",
                "provider_switch_count": max(0, provider_pointer),
                "provider_history": provider_history,
            }
        except TimeoutError:
            last_error = f"子执行超过 {timeout_seconds} 秒未完成"
            last_error_kind = "timeout"
        except Exception as exc:  # pragma: no cover - exercised through scheduler tests
            last_error = str(exc)
            last_error_kind = "failed"

        if provider_order and provider_pointer + 1 < len(provider_order) and attempt <= max_retries:
            provider_pointer += 1
            next_provider = provider_order[provider_pointer]
            route = policy_engine.select_model_for_provider(
                requested_model=model_name,
                selected_provider=next_provider,
                available_models=model_catalog,
            )
            child_payload["provider_name"] = route.get("resolved_provider") or next_provider
            child_payload["model_name"] = route.get("resolved_model") or model_name
            provider_history.append({
                "provider_name": str(child_payload.get("provider_name") or ""),
                "model_name": str(child_payload.get("model_name") or model_name),
                "reason": str(route.get("reason") or "fallback"),
            })

    return child_payload, child_context, "", {
        "status": "failed",
        "retry_count": max(0, attempt - 1),
        "last_error": last_error,
        "error": last_error,
        "error_kind": last_error_kind,
        "provider_switch_count": max(0, provider_pointer),
        "provider_history": provider_history,
    }
