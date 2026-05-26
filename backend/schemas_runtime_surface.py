"""Schemas for runtime-surface read/write APIs."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FailoverThresholdsPayload(BaseModel):
    medium: Optional[float] = None
    high: Optional[float] = None


class RuntimeSurfaceUpdateRequest(BaseModel):
    auth_mode: Optional[str] = None
    default_model: Optional[str] = None
    enabled_providers: Optional[List[str]] = None
    embedded_workspace_store_mode: Optional[str] = None
    failover_thresholds: Optional[FailoverThresholdsPayload] = None


class RuntimeSurfaceEmbeddedRuntimeBootstrapUpdateRequest(BaseModel):
    embedded_workspace_store_mode: Optional[str] = None
    conversation_id: Optional[int] = None


class FrameworkAdapterPilotMessage(BaseModel):
    role: str
    content: str


class FrameworkAdapterPilotRunRequest(BaseModel):
    adapter_id: str
    run_id: str
    messages: List[FrameworkAdapterPilotMessage]
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    execution_context: Optional[dict] = None


class FrameworkAdapterPrecheckRequest(BaseModel):
    adapter_id: str
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    execution_context: Optional[dict] = None


class FrameworkAdapterExternalPilotRunRequest(BaseModel):
    adapter_id: str
    run_id: str
    messages: List[FrameworkAdapterPilotMessage]
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    execution_context: Optional[dict] = None


class RuntimeSurfaceTraceEventSummary(BaseModel):
    event_type: str
    source: Optional[str] = None
    severity: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None


class RuntimeSurfaceApprovalRequestSummary(BaseModel):
    request_id: str
    status: str
    tool_name: Optional[str] = None
    permission_level: Optional[str] = None


class RuntimeSurfaceAuditEventSummary(BaseModel):
    event_type: str
    source: Optional[str] = None
    severity: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None


class RuntimeSurfaceRunOverview(BaseModel):
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    child_run_id: Optional[str] = None
    scheduler_run_id: Optional[str] = None
    run_kind: Optional[str] = None
    status: Optional[str] = None
    trace_count: int = 0
    latest_trace_event: Optional[RuntimeSurfaceTraceEventSummary] = None
    child_merge_intent: Optional[str] = None
    child_merge_entities: List[str] = Field(default_factory=list)
    child_merge_entity_count: int = 0
    child_merge_focus_count: int = 0
    child_merge_action_count: int = 0
    child_merge_primary_entities: List[str] = Field(default_factory=list)
    child_merge_conclusion: Optional[str] = None
    child_merge_section_source: Optional[str] = None
    child_merge_section_ids: List[str] = Field(default_factory=list)
    child_merge_section_counts: dict = Field(default_factory=dict)


class RuntimeSurfaceRunRecovery(BaseModel):
    contract_version: Optional[str] = None
    available: bool = False
    run_id: Optional[str] = None
    run_state: Optional[str] = None
    recoverable: bool = False
    tool_continuation: dict = Field(default_factory=dict)
    loop_continuation: dict = Field(default_factory=dict)
    workspace_backend: dict = Field(default_factory=dict)
    reason: Optional[str] = None


class RuntimeSurfaceEmbeddedRuntimeFactoryProfile(BaseModel):
    db_mode: Optional[str] = None
    embedded_workspace_store_mode: Optional[str] = None
    default_runtime_mode: Optional[str] = None
    recovery_posture: Optional[str] = None


class RuntimeSurfaceEmbeddedRuntimeFactory(BaseModel):
    contract_version: Optional[str] = None
    runtime_backend: Optional[str] = None
    shared_default_runtime: bool = False
    dependency_sources: List[str] = Field(default_factory=list)
    default_runtime_profile: RuntimeSurfaceEmbeddedRuntimeFactoryProfile = Field(default_factory=RuntimeSurfaceEmbeddedRuntimeFactoryProfile)
    workspace_backend: dict = Field(default_factory=dict)
    continuation_registry: dict = Field(default_factory=dict)
    recovery_capabilities: List[str] = Field(default_factory=list)
    factory_methods: List[str] = Field(default_factory=list)


class RuntimeSurfaceChildExecutorPreflight(BaseModel):
    contract_version: Optional[str] = None
    status: Optional[str] = None
    promotion_ready: bool = False
    real_child_executor_ready: bool = False
    executor_binding_status: Optional[str] = None
    executor_binding_blockers: List[str] = Field(default_factory=list)
    recommended_next_step: Optional[str] = None
    delegate_gate_status: Optional[str] = None
    delegate_gate_allowed: bool = False
    delegate_gate_failure_reason: Optional[str] = None
    delegate_promotion_requirements: List[str] = Field(default_factory=list)
    delegate_missing_requirements: List[str] = Field(default_factory=list)
    delegate_non_goals: List[str] = Field(default_factory=list)
    delegate_current_scope: List[str] = Field(default_factory=list)
    backend_registry: dict = Field(default_factory=dict)
    workspace_backend: dict = Field(default_factory=dict)


class RuntimeSurfaceChildExecutorPromotionGate(BaseModel):
    contract_version: Optional[str] = None
    gate_status: Optional[str] = None
    allowed: bool = False
    failure_reason: Optional[str] = None
    executor_path: Optional[str] = None
    recommended_next_step: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)
    checked_at: Optional[str] = None
    child_executor_execution_prerequisites: dict = Field(default_factory=dict)


class RuntimeSurfaceChildExecutorDispatchContract(BaseModel):
    contract_version: Optional[str] = None
    overall_status: Optional[str] = None
    dispatch_ready: bool = False
    will_dispatch: bool = False
    dispatch_mode: Optional[str] = None
    backend_id: Optional[str] = None
    backend_status: Optional[str] = None
    backend_dispatch_ready: bool = False
    gate_allowed: bool = False
    prerequisites_ready: bool = False
    relationship_seam_preserved: bool = True
    blockers: List[str] = Field(default_factory=list)
    child_executor_dispatch_attempt_handoff: dict = Field(default_factory=dict)
    dispatch_attempt_handoff: dict = Field(default_factory=dict)
    recommended_next_step: Optional[str] = None


class RuntimeSurfaceApprovalOverview(BaseModel):
    request_count: int = 0
    pending_count: int = 0
    latest_request: Optional[RuntimeSurfaceApprovalRequestSummary] = None


class RuntimeSurfaceAuditOverview(BaseModel):
    event_count: int = 0
    latest_event: Optional[RuntimeSurfaceAuditEventSummary] = None


class RuntimeSurfaceGovernanceOverviewResponse(BaseModel):
    run: RuntimeSurfaceRunOverview = Field(default_factory=RuntimeSurfaceRunOverview)
    run_recovery: RuntimeSurfaceRunRecovery = Field(default_factory=RuntimeSurfaceRunRecovery)
    child_executor_preflight: RuntimeSurfaceChildExecutorPreflight = Field(default_factory=RuntimeSurfaceChildExecutorPreflight)
    child_executor_promotion_gate: RuntimeSurfaceChildExecutorPromotionGate = Field(default_factory=RuntimeSurfaceChildExecutorPromotionGate)
    child_executor_dispatch_contract: RuntimeSurfaceChildExecutorDispatchContract = Field(default_factory=RuntimeSurfaceChildExecutorDispatchContract)
    approval: RuntimeSurfaceApprovalOverview = Field(default_factory=RuntimeSurfaceApprovalOverview)
    audit: RuntimeSurfaceAuditOverview = Field(default_factory=RuntimeSurfaceAuditOverview)
