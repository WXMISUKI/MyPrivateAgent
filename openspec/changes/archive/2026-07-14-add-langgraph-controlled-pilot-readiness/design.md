## Context

The repository already has:

- `LangGraphDraftAdapter` with health/precheck gates.
- `FrameworkAdapterExternalPilotService` for explicit pilot execution.
- `build_adapter_authoring_checklist(...)` with `authoring_template`.
- Tests proving external pilot execution can run with stub transport when explicitly enabled.

What is missing is the step between "template exists" and "run the external pilot." This change adds a readiness read model that a reviewer or future API can call before running an explicit pilot smoke.

## Goals / Non-Goals

**Goals:**

- Add `build_langgraph_controlled_pilot_readiness(...)` to `FrameworkAdapterRuntimeService`.
- Return a compact `langgraph-controlled-pilot-readiness-v1` contract.
- Fail closed for missing adapter, unsupported adapter, missing package/env, disabled runtime, disabled external pilot, missing authoring template mapping, or default chat boundary drift.
- Keep the method side-effect-free.

**Non-Goals:**

- No external LangGraph call.
- No changes to `execute_external_adapter_run(...)`.
- No default main chat promotion.
- No database writes.
- No frontend surface.
- No AgentRun adapter work.

## Decisions

1. Implement readiness as a method on `FrameworkAdapterRuntimeService`.

   Rationale: this service already owns precheck, authoring checklist, and external pilot execution boundaries. Keeping readiness here prevents a second control path.

2. Scope the first readiness gate to `langgraph_draft`.

   Rationale: LangGraph has existing draft adapter and external pilot code. AgentRun does not yet have an adapter implementation in this repo, so starting there would create infrastructure before evidence.

3. Treat readiness as permission to run an explicit pilot smoke, not execution authorization.

   Rationale: The method returns `can_start_controlled_pilot = true` only when all gates pass, but `will_execute`, `trace_write`, and `audit_write` remain disabled in the readiness check itself.

4. Reuse authoring template evidence.

   Rationale: This directly connects the prior slice to the next pilot step and proves we are following the agreed adapter development discipline.

## Risks / Trade-offs

- [Risk] Teams may still read "ready" as "production ready." -> Mitigation: include `production_promotion = disabled`, `default_chat_entry = disabled`, and next action limited to `run_explicit_controlled_pilot_smoke`.
- [Risk] Gate logic duplicates precheck details. -> Mitigation: summarize precheck and add only pilot-specific blockers.
- [Risk] Overfits to LangGraph. -> Mitigation: this is intentionally the first real external adapter target. Generic adapter template remains separate.

## Migration Plan

1. Add OpenSpec capability.
2. Implement side-effect-free readiness builder.
3. Add focused tests for ready, blocked, unsupported, and unknown paths.
4. Update docs and stage review.
5. Validate OpenSpec and run focused pytest.
6. Archive the change.
