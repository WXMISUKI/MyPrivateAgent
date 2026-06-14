"""Developer-facing agent harness facade.

This module is the high-level embedded entry point for vertical-agent projects.
It intentionally delegates runtime state, events, and approvals to
EmbeddedAgentRuntimeSDK so the facade does not become a second runtime core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable

from .execution_loop import (
    FallbackCallable,
    ModelStepCallable,
    ReflectionCallable,
    ReviewCallable,
    ToolExecutorCallable,
    ToolPolicyCallable,
)
from .runtime_dependencies import (
    EmbeddedRuntimeDependencies,
    EmbeddedRuntimeFactory,
    create_default_embedded_runtime_sdk,
)
from .sdk import EmbeddedAgentRuntimeSDK, build_child_executor_preflight_contract
from .tools import ToolRenderMode, ToolSpec


AGENT_HARNESS_FACADE_METHODS = [
    {
        "method": "run",
        "description": "Create an AgentRun with agent-level defaults.",
        "required_capabilities": ["runtime.run_create"],
        "stability": "preview",
    },
    {
        "method": "stream",
        "description": "Stream AgentEvent records for a run.",
        "required_capabilities": ["runtime.event_stream"],
        "stability": "preview",
    },
    {
        "method": "list_continuation_bindings",
        "description": "Return a read-only catalog of continuation bindings visible to the current harness runtime.",
        "required_capabilities": ["runtime.continuation_binding_catalog"],
        "stability": "preview",
    },
    {
        "method": "probe_recovery",
        "description": "Probe whether a run currently has a recoverable continuation path.",
        "required_capabilities": ["runtime.run_recovery_probe"],
        "stability": "preview",
    },
    {
        "method": "approve",
        "description": "Approve or deny a pending ApprovalRequest.",
        "required_capabilities": ["runtime.approval_submit"],
        "stability": "preview",
    },
    {
        "method": "resume",
        "description": "Resume a run that is ready to continue after approval or observation.",
        "required_capabilities": ["runtime.run_resume"],
        "stability": "preview",
    },
    {
        "method": "delegate",
        "description": "Create a child run under a parent run.",
        "required_capabilities": ["runtime.child_run_create"],
        "stability": "preview",
    },
    {
        "method": "evaluate_delegate_preflight",
        "description": "Evaluate whether a delegated child payload is ready for a future executor binding path.",
        "required_capabilities": ["runtime.child_run_preflight"],
        "stability": "preview",
    },
    {
        "method": "evaluate_delegate_gate",
        "description": "Run the formal execution gate for a delegated child payload without creating a child run.",
        "required_capabilities": ["runtime.child_run_gate"],
        "stability": "preview",
    },
    {
        "method": "evaluate_delegate_routing",
        "description": "Build a no-execute routing decision for a delegated child payload after the execution gate.",
        "required_capabilities": ["runtime.child_run_route"],
        "stability": "preview",
    },
    {
        "method": "bind_delegate_routing",
        "description": "Bind a routed child executor candidate into a record-only handoff contract without executing it.",
        "required_capabilities": ["runtime.child_run_bind"],
        "stability": "preview",
    },
    {
        "method": "execute_delegate_stub",
        "description": "Record a no-execute executor stub result from a bound child executor handoff contract.",
        "required_capabilities": ["runtime.child_run_stub"],
        "stability": "preview",
    },
    {
        "method": "execute_delegate",
        "description": "Run the minimal embedded_sdk_worker executor skeleton for a bound child executor handoff contract.",
        "required_capabilities": ["runtime.child_run_execute"],
        "stability": "preview",
    },
    {
        "method": "merge_delegate_output",
        "description": "Merge a child executor output envelope into the parent run as a minimal merge summary.",
        "required_capabilities": ["runtime.child_run_merge"],
        "stability": "preview",
    },
    {
        "method": "list_delegate_outputs",
        "description": "Replay child executor execution and merge records recorded on a parent run.",
        "required_capabilities": ["runtime.child_run_replay"],
        "stability": "preview",
    },
    {
        "method": "summarize_delegate_outputs",
        "description": "Summarize replayed child executor outputs into a compact artifact summary for consumption surfaces.",
        "required_capabilities": ["runtime.child_run_summary"],
        "stability": "preview",
    },
    {
        "method": "create_artifact",
        "description": "Attach an artifact reference to a run.",
        "required_capabilities": ["runtime.artifact_create"],
        "stability": "preview",
    },
    {
        "method": "list_artifacts",
        "description": "Replay artifact references for a run.",
        "required_capabilities": ["runtime.artifact_read"],
        "stability": "preview",
    },
    {
        "method": "register_tool",
        "description": "Register ToolSpec metadata and an optional local implementation for embedded facade execution.",
        "required_capabilities": ["runtime.tool_register"],
        "stability": "preview",
    },
    {
        "method": "execute",
        "description": "Drive a run through the minimal harness execution loop.",
        "required_capabilities": ["runtime.loop_execute"],
        "stability": "preview",
    },
]


def build_agent_harness_facade_contract() -> Dict[str, Any]:
    return {
        "contract_version": "phase-e-agent-harness-facade-v1",
        "stability": "preview",
        "methods": [dict(item) for item in AGENT_HARNESS_FACADE_METHODS],
        "runtime_backend": "EmbeddedAgentRuntimeSDK",
        "delegate_preflight": build_child_executor_preflight_contract(),
        "facade_runtime_posture": "embedded_harness_v1_candidate",
        "tool_registry_bridge": {
            "local_tool_spec_registry": True,
            "tool_runtime_service_optional": True,
            "runtime_state_owner": "EmbeddedAgentRuntimeSDK",
        },
        "default_tool_executor": {
            "source": "registered_facade_tool",
            "requires_explicit_handler": True,
            "trace_model": "sdk_tool_events",
        },
    }


@dataclass
class AgentHarnessFacade:
    """Small developer-facing facade over the embedded runtime SDK."""

    name: str
    model_name: str = "unknown"
    sdk: EmbeddedAgentRuntimeSDK | None = None
    runtime_factory: EmbeddedRuntimeFactory | None = None
    runtime_dependencies: EmbeddedRuntimeDependencies | None = None
    default_user_id: int | None = None
    default_conversation_id: int | None = None
    default_run_kind: str = "chat"
    tool_runtime_service: Any | None = None
    _registered_tool_specs: Dict[str, ToolSpec] = field(default_factory=dict, init=False, repr=False)
    _registered_tool_handlers: Dict[str, Callable[..., Any]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.name = str(self.name or "").strip()
        if not self.name:
            raise ValueError("agent name is required.")
        self.model_name = str(self.model_name or "unknown").strip() or "unknown"
        self.default_run_kind = str(self.default_run_kind or "chat").strip() or "chat"
        if self.sdk is None:
            if self.runtime_factory is not None:
                self.sdk = self.runtime_factory.create_sdk(runtime_dependencies=self.runtime_dependencies)
            else:
                self.sdk = create_default_embedded_runtime_sdk(runtime_dependencies=self.runtime_dependencies)

    def build_contract(self) -> Dict[str, Any]:
        contract = build_agent_harness_facade_contract()
        contract["agent_name"] = self.name
        contract["tool_registry_bridge"]["registered_tool_count"] = len(self._registered_tool_specs)
        contract["tool_registry_bridge"]["registered_tool_names"] = sorted(self._registered_tool_specs)
        contract["default_tool_executor"]["available"] = bool(self._registered_tool_handlers)
        return contract

    def register_tool(
        self,
        tool: ToolSpec | Dict[str, Any] | None = None,
        *,
        handler: Callable[..., Any] | None = None,
        **tool_fields: Any,
    ) -> Dict[str, Any]:
        tool_spec = self._normalize_tool_spec(tool, **tool_fields)
        self._registered_tool_specs[tool_spec.name] = tool_spec
        if handler is not None:
            self._registered_tool_handlers[tool_spec.name] = handler
        self._register_tool_spec_with_runtime_service(tool_spec)
        return {
            "status": "registered",
            "tool_spec": tool_spec.to_dict(),
            "handler_registered": handler is not None,
            "tool_registry_bridge": {
                "local_tool_spec_registry": True,
                "tool_runtime_service": self.tool_runtime_service is not None,
            },
        }

    def run(self, payload: Dict[str, Any] | str | None = None, **overrides: Any) -> Dict[str, Any]:
        run_payload = self._normalize_run_payload(payload)
        run_payload.update({key: value for key, value in overrides.items() if value is not None})
        run_payload.setdefault("model_name", self.model_name)
        run_payload.setdefault("run_kind", self.default_run_kind)
        if self.default_user_id is not None:
            run_payload.setdefault("user_id", self.default_user_id)
        if self.default_conversation_id is not None:
            run_payload.setdefault("conversation_id", self.default_conversation_id)

        metadata = dict(run_payload.get("metadata") or {})
        metadata.setdefault("agent_name", self.name)
        if "input" in run_payload:
            metadata.setdefault("input", run_payload["input"])
        run_payload["metadata"] = metadata
        return self.sdk.create_run(run_payload)

    def stream(self, run_id: str) -> Iterable[Dict[str, Any]]:
        return self.sdk.stream_events(run_id)

    def list_continuation_bindings(self) -> Dict[str, Any]:
        return self.sdk.list_continuation_bindings()

    def probe_recovery(self, run_id: str) -> Dict[str, Any]:
        return self.sdk.probe_run_recovery(run_id)

    def approve(self, approval_request_id: str, decision: str = "approved") -> Dict[str, Any]:
        return self.sdk.submit_approval(approval_request_id, decision)

    def resume(self, run_id: str, *, continue_loop: bool = False) -> Dict[str, Any]:
        return self.sdk.resume_run(run_id, continue_loop=continue_loop)

    def delegate(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        child_payload = self._normalize_run_payload(payload)
        child_payload.update({key: value for key, value in overrides.items() if value is not None})
        child_payload.setdefault("model_name", self.model_name)
        child_payload.setdefault("run_kind", "child")

        child_agent_name = str(name or "").strip() or f"{self.name}.child"
        metadata = dict(child_payload.get("metadata") or {})
        metadata.setdefault("agent_name", child_agent_name)
        metadata.setdefault("delegated_by_agent", self.name)
        if "input" in child_payload:
            metadata.setdefault("input", child_payload["input"])
        child_payload["metadata"] = metadata
        return self.sdk.delegate_run(parent_run_id, child_payload)

    def evaluate_delegate_preflight(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        child_payload = self._normalize_run_payload(payload)
        child_payload.update({key: value for key, value in overrides.items() if value is not None})
        child_payload.setdefault("model_name", self.model_name)
        child_payload.setdefault("run_kind", "child")

        child_agent_name = str(name or "").strip() or f"{self.name}.child"
        metadata = dict(child_payload.get("metadata") or {})
        metadata.setdefault("agent_name", child_agent_name)
        metadata.setdefault("delegated_by_agent", self.name)
        if "input" in child_payload:
            metadata.setdefault("input", child_payload["input"])
        child_payload["metadata"] = metadata
        return self.sdk.evaluate_child_executor_preflight(child_payload, parent_run_id=parent_run_id)

    def evaluate_delegate_gate(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        child_payload = self._normalize_run_payload(payload)
        child_payload.update({key: value for key, value in overrides.items() if value is not None})
        child_payload.setdefault("model_name", self.model_name)
        child_payload.setdefault("run_kind", "child")

        child_agent_name = str(name or "").strip() or f"{self.name}.child"
        metadata = dict(child_payload.get("metadata") or {})
        metadata.setdefault("agent_name", child_agent_name)
        metadata.setdefault("delegated_by_agent", self.name)
        if "input" in child_payload:
            metadata.setdefault("input", child_payload["input"])
        child_payload["metadata"] = metadata
        return self.sdk.evaluate_child_executor_gate(child_payload, parent_run_id=parent_run_id)

    def evaluate_delegate_routing(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        child_payload = self._normalize_run_payload(payload)
        child_payload.update({key: value for key, value in overrides.items() if value is not None})
        child_payload.setdefault("model_name", self.model_name)
        child_payload.setdefault("run_kind", "child")

        child_agent_name = str(name or "").strip() or f"{self.name}.child"
        metadata = dict(child_payload.get("metadata") or {})
        metadata.setdefault("agent_name", child_agent_name)
        metadata.setdefault("delegated_by_agent", self.name)
        if "input" in child_payload:
            metadata.setdefault("input", child_payload["input"])
        child_payload["metadata"] = metadata
        return self.sdk.evaluate_child_executor_routing(child_payload, parent_run_id=parent_run_id)

    def bind_delegate_routing(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        child_payload = self._normalize_run_payload(payload)
        child_payload.update({key: value for key, value in overrides.items() if value is not None})
        child_payload.setdefault("model_name", self.model_name)
        child_payload.setdefault("run_kind", "child")

        child_agent_name = str(name or "").strip() or f"{self.name}.child"
        metadata = dict(child_payload.get("metadata") or {})
        metadata.setdefault("agent_name", child_agent_name)
        metadata.setdefault("delegated_by_agent", self.name)
        if "input" in child_payload:
            metadata.setdefault("input", child_payload["input"])
        child_payload["metadata"] = metadata
        return self.sdk.bind_child_executor_routing(child_payload, parent_run_id=parent_run_id)

    def execute_delegate_stub(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        binding = self.bind_delegate_routing(
            parent_run_id,
            payload,
            name=name,
            **overrides,
        )
        return self.sdk.execute_bound_child_executor_stub(binding, parent_run_id=parent_run_id)

    def execute_delegate(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        binding = self.bind_delegate_routing(
            parent_run_id,
            payload,
            name=name,
            **overrides,
        )
        return self.sdk.execute_bound_child_executor(binding, parent_run_id=parent_run_id)

    def merge_delegate_output(
        self,
        parent_run_id: str,
        payload: Dict[str, Any] | str | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        execution = self.execute_delegate(
            parent_run_id,
            payload,
            name=name,
            **overrides,
        )
        return self.sdk.merge_child_executor_output(execution, parent_run_id=parent_run_id)

    def list_delegate_outputs(self, parent_run_id: str) -> Dict[str, Any]:
        return self.sdk.list_child_executor_outputs(parent_run_id)

    def summarize_delegate_outputs(self, parent_run_id: str) -> Dict[str, Any]:
        return self.sdk.summarize_child_executor_outputs(parent_run_id)

    def create_artifact(
        self,
        run_id: str,
        *,
        kind: str,
        content: str,
        metadata: Dict[str, Any] | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        artifact_payload = {key: value for key, value in overrides.items() if value is not None}
        artifact_payload["kind"] = kind
        artifact_payload["content"] = content
        artifact_metadata = dict(metadata or {})
        artifact_metadata.setdefault("agent_name", self.name)
        artifact_payload["metadata"] = artifact_metadata
        return self.sdk.create_artifact(run_id, artifact_payload)

    def list_artifacts(self, run_id: str) -> Dict[str, Any]:
        return self.sdk.list_artifacts(run_id)

    def execute(
        self,
        run_id: str,
        *,
        model_step: ModelStepCallable | None = None,
        tool_policy: ToolPolicyCallable | None = None,
        tool_executor: ToolExecutorCallable | None = None,
        reflector: ReflectionCallable | None = None,
        reviewer: ReviewCallable | None = None,
        fallback_handler: FallbackCallable | None = None,
        max_iterations: int = 1,
    ) -> Dict[str, Any]:
        effective_tool_policy = tool_policy
        if tool_policy is not None and self.tool_runtime_service is not None:
            effective_tool_policy = self._bridge_tool_runtime_policy(tool_policy)
        if tool_executor is None and (self._registered_tool_handlers or self.tool_runtime_service is not None):
            decision_holder: Dict[str, Any] = {}
            if effective_tool_policy is not None:
                effective_tool_policy = self._capture_tool_policy_decision(effective_tool_policy, decision_holder)
            tool_executor = self._build_registered_tool_executor(decision_holder)
        return self.sdk.execute_run(
            run_id,
            model_step=model_step,
            tool_policy=effective_tool_policy,
            tool_executor=tool_executor,
            reflector=reflector,
            reviewer=reviewer,
            fallback_handler=fallback_handler,
            max_iterations=max_iterations,
        )

    @staticmethod
    def _normalize_run_payload(payload: Dict[str, Any] | str | None) -> Dict[str, Any]:
        if payload is None:
            return {}
        if isinstance(payload, str):
            return {"input": payload}
        if isinstance(payload, dict):
            return dict(payload)
        raise TypeError("agent run payload must be a dict, string, or None.")

    def _capture_tool_policy_decision(
        self,
        tool_policy: ToolPolicyCallable,
        decision_holder: Dict[str, Any],
    ) -> ToolPolicyCallable:
        def _wrapped(run_context: Any) -> Any:
            raw_decision = tool_policy(run_context)
            if isinstance(raw_decision, dict):
                decision_holder.clear()
                decision_holder.update({
                    "status": str(raw_decision.get("status") or "allowed"),
                    "tool_name": str(raw_decision.get("tool_name") or "").strip(),
                    "tool_args": dict(raw_decision.get("tool_args") or {}),
                    "reason": str(raw_decision.get("reason") or "").strip(),
                    "metadata": dict(raw_decision.get("metadata") or {}),
                })
            return raw_decision

        return _wrapped

    def _bridge_tool_runtime_policy(self, tool_policy: ToolPolicyCallable) -> ToolPolicyCallable:
        def _wrapped(run_context: Any) -> Any:
            raw_decision = tool_policy(run_context)
            decision = self._decision_to_dict(raw_decision)
            if not decision:
                return raw_decision
            if str(decision.get("status") or "allowed").strip().lower() != "allowed":
                return raw_decision
            tool_name = str(decision.get("tool_name") or "").strip()
            if not tool_name:
                return raw_decision
            runtime_decision = self._probe_tool_runtime_policy(tool_name)
            runtime_status = str(runtime_decision.get("status") or "").strip().lower()
            if runtime_status not in {"approval_required", "denied"}:
                return raw_decision
            metadata = dict(decision.get("metadata") or {})
            metadata.update({
                "policy": runtime_decision.get("policy"),
                "permission_level": runtime_decision.get("permission_level"),
                "reason_code": runtime_decision.get("reason_code"),
                "tool_runtime_policy_decision": dict(runtime_decision),
            })
            bridged = {
                "status": runtime_status,
                "tool_name": tool_name,
                "tool_args": dict(decision.get("tool_args") or {}),
                "reason": str(runtime_decision.get("reason") or decision.get("reason") or ""),
                "metadata": metadata,
            }
            return bridged

        return _wrapped

    @staticmethod
    def _decision_to_dict(raw_decision: Any) -> Dict[str, Any]:
        if isinstance(raw_decision, dict):
            return dict(raw_decision)
        to_dict = getattr(raw_decision, "to_dict", None)
        if callable(to_dict):
            return dict(to_dict() or {})
        return {}

    def _probe_tool_runtime_policy(self, tool_name: str) -> Dict[str, Any]:
        evaluate_tool_policy = getattr(self.tool_runtime_service, "evaluate_tool_policy", None)
        if callable(evaluate_tool_policy):
            return dict(evaluate_tool_policy(tool_name) or {})
        return {}

    def _build_registered_tool_executor(self, decision_holder: Dict[str, Any]) -> ToolExecutorCallable:
        def _execute(run_context: Any) -> Dict[str, Any] | None:
            decision = dict(decision_holder or {})
            tool_name = str(decision.get("tool_name") or "").strip()
            tool_args = dict(decision.get("tool_args") or {})
            if not tool_name and len(self._registered_tool_handlers) == 1:
                tool_name = next(iter(self._registered_tool_handlers))
            if not tool_name:
                return None
            handler = self._registered_tool_handlers.get(tool_name)
            if handler is None:
                return self._execute_tool_runtime_service_tool(tool_name, tool_args, run_context=run_context)
            tool_spec = self._registered_tool_specs.get(tool_name)
            result = handler(tool_args)
            result_text = str(result or "")
            action = {
                "type": "tool_action",
                "tool_name": tool_name,
                "args": dict(tool_args),
                "agent_name": self.name,
            }
            observation = {
                "type": "tool_observation",
                "status": "ok",
                "tool_name": tool_name,
                "result_text": result_text,
            }
            return {
                "tool_name": tool_name,
                "args": tool_args,
                "result": result_text,
                "execution": {
                    "executor": "agent_harness_facade_registered_tool",
                    "action": action,
                    "observation": observation,
                    "tool_spec": tool_spec.to_dict() if tool_spec is not None else {},
                },
            }

        return _execute

    def _execute_tool_runtime_service_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        *,
        run_context: Any = None,
    ) -> Dict[str, Any] | None:
        execute_tool = getattr(self.tool_runtime_service, "execute_tool", None)
        if not callable(execute_tool):
            return None
        execution_options = self._build_tool_runtime_execution_options(run_context)
        result = dict(execute_tool(tool_name, tool_args, execution_options=execution_options) or {})
        if not result:
            return None
        return {
            "tool_name": str(result.get("tool_name") or tool_name),
            "args": dict(result.get("args") or tool_args),
            "result": str(result.get("result_text") or ""),
            "execution": dict(result.get("execution") or {}),
        }

    @staticmethod
    def _build_tool_runtime_execution_options(run_context: Any = None) -> Dict[str, Any]:
        metadata = dict(getattr(run_context, "metadata", {}) or {})
        approved = dict(metadata.get("approved_tool_execution") or {})
        if str(approved.get("decision") or "").strip().lower() != "approved":
            return {}
        return {
            "policy_override": {
                "status": "approved",
                "approval_request_id": str(approved.get("approval_request_id") or "").strip(),
                "source": str(approved.get("source") or "embedded_sdk_tool_continuation").strip(),
            }
        }

    def _register_tool_spec_with_runtime_service(self, tool_spec: ToolSpec) -> None:
        registry = getattr(self.tool_runtime_service, "tool_registry", None)
        register_tool_spec = getattr(registry, "register_tool_spec", None)
        if callable(register_tool_spec):
            register_tool_spec(tool_spec)

    @staticmethod
    def _normalize_tool_spec(tool: ToolSpec | Dict[str, Any] | None = None, **tool_fields: Any) -> ToolSpec:
        if isinstance(tool, ToolSpec):
            if tool_fields:
                data = tool.to_dict()
                data.update(tool_fields)
                return ToolSpec(**data)
            return tool
        data = dict(tool or {})
        data.update({key: value for key, value in tool_fields.items() if value is not None})
        name = str(data.get("name") or "").strip()
        description = str(data.get("description") or "").strip()
        if not name:
            raise ValueError("tool name is required.")
        if not description:
            raise ValueError("tool description is required.")
        render_mode = data.get("render_mode") or ToolRenderMode.PLAIN_TEXT
        if not isinstance(render_mode, ToolRenderMode):
            render_mode = ToolRenderMode(str(render_mode or ToolRenderMode.PLAIN_TEXT.value))
        return ToolSpec(
            name=name,
            description=description,
            permission_level=str(data.get("permission_level") or "auto"),
            deterministic=bool(data.get("deterministic", False)),
            safe_to_rephrase=bool(data.get("safe_to_rephrase", True)),
            render_mode=render_mode,
            supports_cache=bool(data.get("supports_cache", False)),
            cache_ttl_seconds=data.get("cache_ttl_seconds"),
            timeout_seconds=data.get("timeout_seconds"),
            passthrough_strategy=str(data.get("passthrough_strategy") or "never"),
            card_schema=data.get("card_schema"),
            supported_card_schemas=tuple(data.get("supported_card_schemas") or ()),
            tags=tuple(data.get("tags") or ()),
        )


def create_agent(
    *,
    name: str,
    model_name: str = "unknown",
    sdk: EmbeddedAgentRuntimeSDK | None = None,
    runtime_factory: EmbeddedRuntimeFactory | None = None,
    runtime_dependencies: EmbeddedRuntimeDependencies | None = None,
    default_user_id: int | None = None,
    default_conversation_id: int | None = None,
    default_run_kind: str = "chat",
    tool_runtime_service: Any | None = None,
) -> AgentHarnessFacade:
    return AgentHarnessFacade(
        name=name,
        model_name=model_name,
        sdk=sdk,
        runtime_factory=runtime_factory,
        runtime_dependencies=runtime_dependencies,
        default_user_id=default_user_id,
        default_conversation_id=default_conversation_id,
        default_run_kind=default_run_kind,
        tool_runtime_service=tool_runtime_service,
    )
