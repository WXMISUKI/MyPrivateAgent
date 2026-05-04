"""Smoke check for multi-agent scheduler + policy trace flow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from services.chat_service import stream_scheduled_orchestrator_events
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.chat_service import stream_scheduled_orchestrator_events


class _StubPlannerService:
    def __init__(self, _db):
        self.plan = SimpleNamespace(
            id=101,
            active_item_id=501,
            items=[
                SimpleNamespace(
                    id=501,
                    title="并发执行前后端任务",
                    details="",
                    status="in_progress",
                    item_metadata={},
                    handoff_status=SimpleNamespace(value="executing"),
                )
            ],
        )

    def get_latest_plan_for_conversation(self, *, user_id, conversation_id):
        return self.plan

    def get_active_item(self, *, plan):
        return plan.items[0]

    def serialize_plan(self, plan):
        return {"id": plan.id, "active_item_id": plan.active_item_id}


class _StubSchedulerService:
    def __init__(self, _db):
        self.completed = []
        self.failed = []

    def mark_child_running(self, **_kwargs):
        return None

    def mark_child_policy_selected(self, **_kwargs):
        return None

    def mark_child_completed(self, *, child_execution_id, output_text, **_kwargs):
        self.completed.append((child_execution_id, output_text))
        return None

    def mark_child_failed(self, *, child_execution_id, error_text, **_kwargs):
        self.failed.append((child_execution_id, error_text))
        return None

    def mark_child_retrying(self, **_kwargs):
        return None

    def mark_child_cancelled(self, **_kwargs):
        return None

    def get_execution_policy(self, _item):
        return {"timeout_seconds": 2, "max_retries": 0, "cancel_on_failure": False}

    def append_audit_event(self, **_kwargs):
        return None

    def append_run_trace_event(self, **_kwargs):
        return None

    def merge_child_outputs(self, **_kwargs):
        merged_output = "\n".join(text for _cid, text in self.completed)
        return {
            "merge_status": "completed" if self.completed else "failed",
            "merged_output": merged_output,
            "completed_children": len(self.completed),
            "failed_children": len(self.failed),
            "pending_children": 0,
        }


class _StubSubagentService:
    @staticmethod
    def normalize_context(payload):
        return SimpleNamespace(
            agent_role=payload.get("agent_role"),
            agent_id=payload.get("agent_id"),
            plan_id=payload.get("plan_id"),
            plan_item_id=payload.get("plan_item_id"),
            plan_item_title=payload.get("plan_item_title"),
        )

    @staticmethod
    def build_spawn_event(context):
        return {"type": "status", "status_kind": "subagent_spawned", "agent_role": context.agent_role}

    @staticmethod
    def build_collect_event(context, *, output_text):
        return {
            "type": "status",
            "status_kind": "subagent_collected",
            "agent_role": context.agent_role,
            "subagent_output_excerpt": output_text[:32],
        }


class _StubPolicyEngine:
    @staticmethod
    def select_provider_hint(*, requested_model, context):
        role = (context or {}).get("agent_role") or "general"
        return {
            "selected_provider": "volcengine-ark" if role in {"backend", "frontend"} else "anthropic",
            "reason": "default_provider_order",
            "model_name": requested_model,
            "agent_role": role,
        }

    @staticmethod
    def select_model_for_provider(*, requested_model, selected_provider, available_models):
        provider = str(selected_provider or "")
        for item in available_models or []:
            if str(item.get("provider") or "") == provider:
                return {
                    "resolved_model": item.get("name") or requested_model,
                    "resolved_provider": provider,
                    "reason": "provider_fallback_model_selected",
                }
        return {
            "resolved_model": requested_model,
            "resolved_provider": provider,
            "reason": "provider_not_found_keep_requested_model",
        }


class _StubOrchestrator:
    def __init__(self, label):
        self.label = label

    async def process_message(self, user_message: str, selected_model: str, execution_context=None):
        yield json.dumps({"type": "content", "content": f"{self.label}: {user_message}"}, ensure_ascii=False)
        yield json.dumps({"type": "done", "content": f"{self.label}: {selected_model}"}, ensure_ascii=False)


def _stub_orchestrator_factory(*, conversation_id, show_reasoning):
    return _StubOrchestrator(label=f"child-{conversation_id}-{int(bool(show_reasoning))}")


async def _run() -> None:
    from unittest.mock import patch

    with (
        patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerService),
        patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerService),
        patch("backend.services.subagent_service.get_subagent_runtime_service", return_value=_StubSubagentService()),
        patch("backend.services.chat_service._get_policy_engine_service", return_value=_StubPolicyEngine()),
        patch("backend.services.chat_service._get_orchestrator_factory", return_value=_stub_orchestrator_factory),
    ):
        events = []
        async for chunk, _actual in stream_scheduled_orchestrator_events(
            orchestrator=SimpleNamespace(show_reasoning=False),
            db=object(),
            user_id=1,
            conversation_id=9,
            user_message="执行并汇总",
            model_name="doubao",
            execution_context={
                "scheduler_mode": "fan_out",
                "scheduler_run_id": "sched-p101-i501",
                "plan_id": 101,
                "plan_item_id": 501,
                "child_contexts": [
                    {
                        "plan_id": 101,
                        "plan_item_id": 501,
                        "plan_item_title": "并发执行前后端任务",
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p101-i501-c1",
                        "child_execution_id": "backend-child-p101-i501-c1",
                    },
                    {
                        "plan_id": 101,
                        "plan_item_id": 501,
                        "plan_item_title": "并发执行前后端任务",
                        "agent_role": "frontend",
                        "agent_id": "frontend-agent-p101-i501-c2",
                        "child_execution_id": "frontend-child-p101-i501-c2",
                    },
                ],
            },
        ):
            events.append(chunk)

    joined = "\n".join(events)
    assert "subagent_policy_selected" in joined
    assert "scheduler_merged" in joined
    assert '"type": "done"' in joined
    print("PASS: multi_agent_policy_smoke")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run())
