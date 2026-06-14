## Context

`ExecutionLoopController` already emits review and fallback events when callers pass reviewer or fallback callables through `AgentHarnessFacade` / `EmbeddedAgentRuntimeSDK.execute_run(...)`. Existing tests cover behavior, but the SDK contract does not explicitly list reviewer/fallback event status kinds and required payloads.

This makes governance consumers depend on implicit event shapes. The hardening step should expose those shapes in `build_embedded_sdk_contract()` and ensure `validate_embedded_sdk_event_payloads(...)` catches missing review/fallback payloads.

## Goals / Non-Goals

**Goals:**

- Declare reviewer/fallback status kinds in Embedded SDK event contract.
- Preserve required payloads for `review`, `fallback`, `error`, `loop_step`, and `run` where applicable.
- Add focused tests using real SDK/harness events.
- Keep execution behavior unchanged.

**Non-Goals:**

- No real LLM execution.
- No default chat integration.
- No new persistence model.
- No new reviewer registry.
- No frontend work.

## Decisions

1. Harden event contract before changing behavior.

   Rationale: behavior already exists and tests pass; the missing piece is contract visibility for governance and quality gates.

2. Use existing status kinds.

   Rationale: `execution_loop_reviewed`, `execution_loop_review_rejected`, `execution_loop_fallback_applied`, and `execution_loop_failed` already appear in emitted events. Declaring them avoids event-name churn.

3. Keep fallback handled vs fail-closed distinct.

   Rationale: handled fallback can let the run continue, while unhandled fallback fails closed. Governance consumers need to distinguish those outcomes.

## Risks / Trade-offs

- More status kinds increase snapshot surface -> mitigate with focused payload validation tests.
- Existing event payloads may be missing fields -> add the smallest fields already emitted by the controller rather than changing event flow.
- Contract hardening can expose old generated events as incomplete -> acceptable because it helps catch drift in quality gates.
