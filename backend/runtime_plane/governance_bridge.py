"""
Governance Bridge - 运行层→治理层桥接

连接运行层执行事件和治理层的 policy/approval/trace/audit。
这是 MyPrivateAgent 控制面的核心价值：外部框架执行，我们治理。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from .contracts import AgentManifest, ExecutionEvent, ExecutionRequest, ExecutionResult

logger = logging.getLogger(__name__)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _stage_counts(events: list[ExecutionEvent]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        stage = _clean_str(event.stage) or "unknown"
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def _find_approval_event(events: list[ExecutionEvent]) -> ExecutionEvent | None:
    for event in events:
        if _clean_str(event.type).lower() == "approval_required":
            return event
        if _clean_str(event.stage).lower() == "approval":
            return event
    return None


def build_runtime_plane_governance_projection(
    *,
    request: ExecutionRequest,
    manifest: AgentManifest,
    events: list[ExecutionEvent],
    result: ExecutionResult,
    adapter_id: str,
) -> dict[str, Any]:
    """Build a compact, side-effect-free governance read model.

    This projection is intentionally not a trace writer. It gives future
    governance surfaces one stable summary of runtime-plane adapter envelopes.
    """
    approval_event = _find_approval_event(events)
    approval_metadata = dict(approval_event.metadata) if approval_event else {}
    approval_required = bool(approval_event) or result.status == "approval_pending"
    approval_tool_name = _clean_str(approval_metadata.get("tool_name")) or None
    tool_call_count = len(result.tool_calls)

    return {
        "read_model": "runtime_plane_governance_projection",
        "contract_version": "runtime-plane-governance-read-model-v1",
        "request_id": request.request_id,
        "run_id": events[0].run_id if events else request.request_id,
        "agent_id": request.agent_id,
        "manifest_agent_id": manifest.agent_id,
        "runtime": request.runtime,
        "adapter_id": adapter_id,
        "result_status": result.status,
        "trace_ref": result.trace_ref,
        "event_count": len(events),
        "stage_counts": _stage_counts(events),
        "tool_call_count": tool_call_count,
        "approval_required": approval_required,
        "approval_tool_name": approval_tool_name,
        "approval_status": "required" if approval_required else "not_required",
        "boundaries": {
            "read_model_only": True,
            "will_persist_trace": False,
            "will_submit_approval": False,
            "default_chat_changed": False,
        },
    }


class GovernanceBridge:
    """运行层与治理层的桥梁。

    职责：
    1. 工具调用前检查策略（policy engine）
    2. 高风险工具触发审批（approval engine）
    3. 执行事件记录到 trace
    4. 审计事件记录到 audit

    Usage:
        bridge = GovernanceBridge(policy_engine, approval_engine, trace_service)

        # 在工具调用前检查
        decision = bridge.on_tool_call("execute_refund", {"amount": 1000})
        if decision["status"] == "approval_required":
            # 等待审批
            approval_result = bridge.wait_for_approval(decision["approval_id"])
    """

    def __init__(
        self,
        policy_engine=None,
        approval_engine=None,
        trace_service=None,
        audit_service=None,
    ):
        self.policy_engine = policy_engine
        self.approval_engine = approval_engine
        self.trace_service = trace_service
        self.audit_service = audit_service

    def on_tool_call(self, tool_name: str, tool_args: dict, context: dict = None) -> dict:
        """工具调用前检查策略。

        Returns:
            {"status": "allowed"} 或
            {"status": "approval_required", "approval_id": "..."} 或
            {"status": "denied", "reason": "..."}
        """
        # 如果没有策略引擎，允许所有调用
        if not self.policy_engine:
            return {"status": "allowed"}

        try:
            decision = self.policy_engine.evaluate_tool_use(
                tool_name=tool_name,
                tool_args=tool_args,
                context=context or {},
            )

            if decision.get("status") == "approval_required" and self.approval_engine:
                # 创建审批请求
                approval = self.approval_engine.create_request(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    context=context,
                )
                return {
                    "status": "approval_required",
                    "approval_id": approval.get("id", str(uuid.uuid4())),
                }

            return decision

        except Exception as e:
            logger.error(f"Policy check error for tool '{tool_name}': {e}")
            return {"status": "allowed"}  # fail-open for now

    def on_event(self, event: dict) -> None:
        """记录执行事件到 trace。"""
        if not self.trace_service:
            return

        try:
            self.trace_service.record_event(
                event_type=event.get("type", "unknown"),
                payload=event.get("data", {}),
                run_id=event.get("run_id"),
                node_name=event.get("node_name"),
            )
        except Exception as e:
            logger.error(f"Trace recording error: {e}")

    def on_error(self, error: Exception, context: dict = None) -> None:
        """记录错误到审计。"""
        if self.audit_service:
            try:
                self.audit_service.record_error(
                    error_type=type(error).__name__,
                    error_message=str(error),
                    context=context or {},
                )
            except Exception as e:
                logger.error(f"Audit recording error: {e}")

    def wait_for_approval(self, approval_id: str) -> dict:
        """等待审批结果。"""
        if not self.approval_engine:
            return {"status": "approved", "reason": "No approval engine configured"}

        try:
            return self.approval_engine.wait_for_decision(approval_id)
        except Exception as e:
            logger.error(f"Approval wait error: {e}")
            return {"status": "error", "reason": str(e)}

    def on_run_start(self, run_id: str, agent_id: str, user_input: str) -> None:
        """运行开始事件。"""
        self.on_event({
            "type": "run_started",
            "run_id": run_id,
            "data": {"agent_id": agent_id, "user_input": user_input},
        })

    def on_run_end(self, run_id: str, result: dict) -> None:
        """运行结束事件。"""
        self.on_event({
            "type": "run_completed",
            "run_id": run_id,
            "data": {"result_summary": str(result)[:500]},
        })

    def on_node_start(self, run_id: str, node_name: str) -> None:
        """节点开始事件。"""
        self.on_event({
            "type": "node_started",
            "run_id": run_id,
            "node_name": node_name,
            "data": {},
        })

    def on_node_end(self, run_id: str, node_name: str, result: dict) -> None:
        """节点结束事件。"""
        self.on_event({
            "type": "node_completed",
            "run_id": run_id,
            "node_name": node_name,
            "data": {"result_keys": list(result.keys()) if result else []},
        })

    def project_execution_envelope(
        self,
        *,
        request: ExecutionRequest,
        manifest: AgentManifest,
        events: list[ExecutionEvent],
        result: ExecutionResult,
        adapter_id: str,
    ) -> dict[str, Any]:
        """Return the read-only governance projection for an adapter envelope."""
        return build_runtime_plane_governance_projection(
            request=request,
            manifest=manifest,
            events=events,
            result=result,
            adapter_id=adapter_id,
        )
