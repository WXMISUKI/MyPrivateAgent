"""Smoke check for provider failover in multi-agent scheduled execution."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.chat_service import stream_scheduled_orchestrator_events


class _StubPlannerService:
    def __init__(self, _db):
        self.plan = SimpleNamespace(
            id=201,
            active_item_id=601,
            items=[
                SimpleNamespace(
                    id=601,
                    title="provider failover 验证",
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

    def mark_child_policy_selected(self, **_kwargs):
        return None

    def mark_child_running(self, **_kwargs):
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
        return {"timeout_seconds": 2, "max_retries": 1, "cancel_on_failure": False}

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


class _StubPolicyEngine:
    @staticmethod
    def select_provider_hint(*, requested_model, context):
        return {
            "selected_provider": "volcengine-ark",
            "provider_order": ["volcengine-ark", "ollama"],
            "reason": "default_provider_order",
            "model_name": requested_model,
            "agent_role": (context or {}).get("agent_role"),
        }

    @staticmethod
    def select_model_for_provider(*, requested_model, selected_provider, available_models):
        if selected_provider == "ollama":
            return {"resolved_model": "llama3.1", "resolved_provider": "ollama", "reason": "provider_fallback_model_selected"}
        return {"resolved_model": "doubao", "resolved_provider": "volcengine-ark", "reason": "requested_model_matches_provider"}


async def _run() -> None:
    from unittest.mock import patch

    attempts = {"count": 0}

    async def _fake_collect_orchestrator_response(
        *,
        orchestrator,
        user_message,
        model_name,
        execution_context=None,
        db=None,
        user_id=None,
        conversation_id=None,
    ):
        attempts["count"] += 1
        if model_name == "doubao":
            raise RuntimeError("primary provider failed")
        return "fallback-ok"

    with (
        patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerService),
        patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerService),
        patch("backend.services.chat_service._get_policy_engine_service", return_value=_StubPolicyEngine()),
        patch("backend.services.chat_service.collect_orchestrator_response", side_effect=_fake_collect_orchestrator_response),
    ):
        events = []
        async for chunk, _actual in stream_scheduled_orchestrator_events(
            orchestrator=SimpleNamespace(show_reasoning=False, model_provider=SimpleNamespace(list_available_models=lambda: {
                "doubao": {"name": "doubao", "provider": "volcengine-ark", "available": True, "is_default": True},
                "llama3.1": {"name": "llama3.1", "provider": "ollama", "available": True, "is_default": True},
            })),
            db=object(),
            user_id=1,
            conversation_id=9,
            user_message="执行并汇总",
            model_name="doubao",
            execution_context={
                "scheduler_mode": "fan_out",
                "scheduler_run_id": "sched-p201-i601",
                "plan_id": 201,
                "plan_item_id": 601,
                "child_contexts": [
                    {
                        "plan_id": 201,
                        "plan_item_id": 601,
                        "plan_item_title": "provider failover 验证",
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p201-i601-c1",
                        "child_execution_id": "backend-child-p201-i601-c1",
                    },
                ],
            },
        ):
            events.append(chunk)

    joined = "\n".join(events)
    assert attempts["count"] >= 2
    assert "subagent_provider_switched" in joined
    assert "scheduler_merged" in joined
    assert '"type": "done"' in joined
    print("PASS: multi_agent_provider_failover_smoke")


if __name__ == "__main__":
    asyncio.run(_run())

