## Design

### Kernel Contract

The recovery approval kernel keeps `ApprovalEngineService` as the lifecycle authority and `EmbeddedAgentRuntimeSDK` as the runtime coordinator.

- `ApprovalEngineService.submit_approval_decision(...)` owns state transition semantics.
- `EmbeddedAgentRuntimeSDK.submit_approval(...)` owns continuation consume/discard behavior and event emission.
- `probe_run_recovery()` owns entrypoint availability and machine-readable recovery reason.
- `RuntimeSurfaceService.get_run_recovery(...)` consumes the same probe contract instead of creating a second interpretation.

### Recovery Reason Policy

Stable recovery reasons are backend contract values, not display copy:

- `ready_via_registry`
- `ready_in_process`
- `state_gated`
- `missing_registered_binding`
- `workspace_backend_fallback_active`
- `workspace_backend_not_durable`
- `descriptor_missing`
- `already_resolved`
- `denied`

`blocked_reason` remains as a compatibility/debug detail, but consumers should use `recovery_reason` for contract-level routing.

### External Reference Alignment

- Borrow OpenHands' event-driven action/observation separation, but do not introduce a Docker sandbox in this change.
- Borrow LangGraph's checkpoint/interrupt/resume vocabulary only as a persistence/recovery mental model; do not convert the runtime into a graph.
- Borrow Goose's restricted subagent principle for future child executor work; do not implement auto-spawn in this change.
- Borrow Aider's test/git feedback loop as future quality gate inspiration; do not turn this project into a CLI pair-programming product.

### Compatibility

Existing callers that read `blocked_reason` continue to work. This change adds stronger `recovery_reason` semantics and smoke coverage without removing existing fields.
