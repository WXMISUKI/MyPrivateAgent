## Design

The durable checkpoint/resume contract is a backend runtime contract, not a frontend display model. It extends the existing durable workspace state contract and recovery reason vocabulary without changing the ownership model:

- `EmbeddedRunWorkspaceStore` owns persisted checkpoint records and backend capability descriptions.
- `EmbeddedAgentRuntimeSDK` owns recovery coordination, approval/continuation lifecycle, and resume execution gates.
- `RuntimeSurfaceService.get_run_recovery(...)` exposes a read model for operators and governance consumers.
- `runtime_contract_smoke.py` proves the contract using executable samples.

## Checkpoint Contract

A checkpoint is the durable description of a recoverable runtime point. It may include:

```json
{
  "contract_version": "phase-ii-durable-runtime-checkpoint-v1",
  "run_id": "run_123",
  "checkpoint_id": "chk_123",
  "checkpoint_kind": "approval_waiting",
  "run_state": "waiting_approval",
  "event_cursor": {
    "last_event_id": "evt_123",
    "last_sequence": 12
  },
  "approval_ref": {
    "approval_id": "approval_123",
    "status": "pending"
  },
  "continuation_descriptor_ref": {
    "descriptor_kind": "tool_approval_continuation",
    "descriptor_status": "pending",
    "binding_id": "tool:search"
  },
  "workspace_backend": {
    "durable": true,
    "fallback_active": false
  }
}
```

The checkpoint must not contain executable callables, Python function references, active stream iterators, or provider-specific client objects.

## Resume Cursor Contract

A resume cursor is a machine-readable pointer to the next allowed recovery action:

```json
{
  "contract_version": "phase-ii-runtime-resume-cursor-v1",
  "cursor_id": "cursor_123",
  "run_id": "run_123",
  "checkpoint_id": "chk_123",
  "entrypoint": "submit_approval.approved",
  "cursor_status": "ready",
  "recovery_reason": "ready_via_registry",
  "blocked_reason": null,
  "requires_registry_binding": true,
  "requires_durable_workspace": true
}
```

The cursor is an instruction boundary, not a promise that the next action already executed. Actual execution still goes through SDK approval/recovery gates.

## Recovery Alignment

Existing recovery reasons remain valid. This change adds checkpoint/cursor alignment without weakening fail-closed behavior:

- `ready_via_registry`: durable checkpoint and registry binding are both available.
- `state_gated`: checkpoint exists, but current run/approval state makes the requested entrypoint invalid.
- `checkpoint_missing`: no durable checkpoint can be found for the run.
- `resume_cursor_missing`: checkpoint exists but no entrypoint cursor can be derived.
- `resume_cursor_stale`: cursor points to a resolved or superseded checkpoint.
- `workspace_backend_fallback_active`: backend is not a durable recovery source even if descriptors exist.
- `missing_registered_binding`: cursor requires a binding not available in the current process.
- `already_resolved`: approval state is resolved and cannot be submitted again.
- `denied`: approval was denied and execution must not resume.

## External Reference Policy

- Borrow from LangGraph: checkpoint / interrupt / resume cursor vocabulary and fault-tolerant execution semantics.
- Do not borrow from LangGraph: graph orchestration, node/edge runtime, or graph persistence model.
- Borrow from OpenHands: action/observation separation for recovered tool execution traces.
- Do not borrow from OpenHands: Docker/runtime product shell in this phase.
- Borrow from Goose: explicit timeout, max turns, and permission boundary language for future child executors.
- Do not borrow from Goose: automatic subagent expansion.

## Compatibility

Existing `workspace_backend.state_contract` remains the lower-level storage capability contract. The checkpoint/resume cursor contract sits above it and answers whether a specific run has enough durable state to resume.

Existing consumers may continue reading `recoverable / recovery_reason / recovery_entrypoints`. New consumers should prefer the richer checkpoint and resume cursor fields when present.
