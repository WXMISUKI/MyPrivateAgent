## Context

Existing code already has two separate parts:

- `build_langgraph_controlled_pilot_readiness(...)`: side-effect-free permission to start a controlled pilot.
- `execute_external_adapter_run(...)`: explicit external pilot execution through configured transport, trace/audit recorder, and optional Query Control timeline recorder.

The missing piece is a governed smoke wrapper that composes them and returns one compact acceptance report. This prevents callers from bypassing the readiness gate while still reusing the existing execution path.

## Goals / Non-Goals

**Goals:**

- Add a single explicit smoke method on `FrameworkAdapterRuntimeService`.
- Block before external calls when readiness is not ready.
- Reuse `execute_external_adapter_run(...)` when readiness is ready.
- Return machine-readable `smoke_status`, `acceptance`, `readiness`, `pilot_result`, `blockers`, and `boundaries`.
- Keep the method testable with stub transport.

**Non-Goals:**

- No new API route.
- No default main chat promotion.
- No new persistence model.
- No background worker or scheduler.
- No local graph/checkpoint/sandbox implementation.
- No AgentRun adapter.

## Decisions

1. Put the smoke wrapper in `FrameworkAdapterRuntimeService`.

   Rationale: the service already owns readiness and explicit external pilot execution. Keeping the wrapper here avoids a parallel pilot path.

2. Return blocked reports instead of raising when readiness is blocked.

   Rationale: smoke readiness is an acceptance gate; consumers need a machine-readable report. Existing `execute_external_adapter_run(...)` can still raise for direct misuse.

3. Treat failed external pilot execution as a completed smoke with failed acceptance.

   Rationale: connectivity/protocol failures are useful pilot evidence. The existing execution path already normalizes these failures into events and trace/audit evidence.

4. Keep production boundaries explicit in every report.

   Rationale: a successful smoke proves only the controlled pilot path, not production runtime readiness.

## Risks / Trade-offs

- [Risk] Smoke success could be mistaken for production readiness. -> Mitigation: include `production_promotion = disabled` and `default_chat_entry = disabled`.
- [Risk] Wrapper could duplicate external pilot logic. -> Mitigation: delegate execution to `execute_external_adapter_run(...)` and only summarize.
- [Risk] Readiness invocation can run precheck logic multiple times. -> Mitigation: acceptable for a low-cost explicit smoke gate; no external call occurs before readiness passes.

## Migration Plan

1. Add OpenSpec capability.
2. Implement smoke wrapper.
3. Add focused tests for ready success, readiness blocked, and external failure evidence.
4. Update docs and review.
5. Validate and archive.
