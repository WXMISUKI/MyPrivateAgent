## Context

Current SDK approval lifecycle state is already machine-readable and tested:

- `ApprovalEngineService.submit_approval_decision(...)` owns accepted/replayed/ignored decisions.
- `EmbeddedAgentRuntimeSDK.submit_approval(...)` emits SDK status events.
- Runtime contract smoke verifies approval replay/ignored and recovery alignment evidence.
- `RunTraceService` already provides a platform trace/audit seam with dedupe-key support.

The missing boundary is a small adapter that can mirror selected SDK approval lifecycle evidence into governance trace without making trace persistence part of SDK correctness.

## Goals / Non-Goals

**Goals:**

- Add a dedicated SDK approval lifecycle trace adapter contract.
- Make recording opt-in and fail-open.
- Keep event payload compact and machine-readable.
- Reuse existing trace service and dedupe-key seam.
- Cover resolved, replayed, ignored, and recovery fail-closed paths.

**Non-Goals:**

- No broad SDK event recorder.
- No frontend change in this slice.
- No approval state machine rewrite.
- No durable continuation execution change.
- No new database schema unless implementation proves the current trace seam cannot carry the evidence.

## Decisions

### Decision 1: Adapter records selected lifecycle evidence only

The adapter will target approval lifecycle status kinds:

- `approval_resolved`
- `approval_replayed`
- `approval_ignored`
- `recovery_failed_closed`

Rationale: these are the governance-relevant approval lifecycle transitions. Tool result, model, and generic SDK events remain outside this slice.

### Decision 2: Recording is opt-in and fail-open

SDK callers must explicitly provide a recorder/timeline service context. If recording fails, SDK execution continues and the SDK event stream remains the source of truth.

Rationale: governance trace is observability, not execution ownership.

### Decision 3: Dedupe key is stable and compact

Trace payload should include a deterministic dedupe key shaped around source, run id, approval request id, status kind, and decision where available.

Rationale: replay/ignored lifecycle events can be called repeatedly; governance trace must avoid duplicate pollution.

### Decision 4: Recovery reason semantics stay owned by recovery protocol

The trace adapter may mirror `recovery_reason` and `blocked_reason`, but it must not reinterpret them.

Rationale: `runtime-recovery-approval-kernel` and `embedded-sdk-recovery-protocol` already define recovery reason semantics.

## Risks / Trade-offs

- [Risk] SDK constructor grows too broad.  
  Mitigation: inject a small recorder object/callable rather than DB-specific dependencies directly where possible.

- [Risk] Governance trace payload becomes too large.  
  Mitigation: copy only ids, status kind, decision, approval status, recovery reason, blocked reason, and compact persistence evidence if present.

- [Risk] Replayed approvals duplicate trace entries.  
  Mitigation: use `RunTraceService.has_runtime_trace_dedupe_key(...)` before appending.

## Migration Plan

1. Add specs and focused tests for adapter behavior.
2. Add a small lifecycle recorder service/helper.
3. Wire SDK status event emission path to invoke the recorder only when configured.
4. Keep failures isolated and visible in returned recorder metadata when practical.
5. Update docs and manual verification notes.

Rollback is straightforward because the adapter adds optional observability and does not remove SDK events or change approval decisions.

