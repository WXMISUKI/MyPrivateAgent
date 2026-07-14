## Context

The runtime plane has a stable local MVP envelope:

- `ExecutionRequest`
- `AgentManifest`
- `ExecutionEvent`
- `ExecutionResult`

The adapters can now prove simple model responses, read-only tool calls, and high-risk approval interrupts. What is missing is a common governance-facing read model that summarizes these envelopes without exposing raw framework payloads or writing trace/audit state.

## Goals / Non-Goals

**Goals:**

- Add a compact projection that governance consumers can inspect.
- Reuse existing runtime-plane contracts.
- Include the projection in adapter outputs so tests and future surfaces can consume one shape.
- Keep the projection deterministic and side-effect-free.

**Non-Goals:**

- Do not call `RunTraceService`, `ApprovalEngineService`, `AuditService`, or Runtime Surface service.
- Do not create a database model.
- Do not add a frontend panel.
- Do not change default `/api/chat`.
- Do not interpret the projection as production promotion.

## Decisions

### 1. Build projection in `governance_bridge.py`

The projection belongs near `GovernanceBridge` because it defines how runtime-plane signals become governance-readable, but it will be implemented as a pure function and a side-effect-free method.

Alternative considered: create a new service under `backend/services`. Rejected for this slice because runtime-plane local adapters should remain testable without pulling in service-layer dependencies.

### 2. Add `governance_projection` to adapter envelope output

Each adapter already returns a dict envelope. Adding a top-level compact projection keeps the behavior easy to test and avoids a new API surface.

Alternative considered: only expose a separate bridge method. Rejected because future adapter authors need to see the expected output shape directly in the reference adapters.

### 3. Keep boundaries explicit

The projection will include `read_model_only = true`, `will_persist_trace = false`, `will_submit_approval = false`, and `default_chat_changed = false`.

Rationale: this prevents accidental interpretation of read-only visibility as production governance execution.

## Risks / Trade-offs

- [Risk] Consumers may treat the projection as an authoritative persisted trace. -> Mitigation: include explicit boundary flags and docs.
- [Risk] Projection fields may grow too quickly. -> Mitigation: keep this slice limited to compact counts and identity fields.
- [Risk] Adapter output shape changes may affect tests. -> Mitigation: add focused tests and avoid removing existing fields.
