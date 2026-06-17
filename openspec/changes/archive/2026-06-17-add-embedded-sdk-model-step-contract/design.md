## Context

`ExecutionLoopController` already owns observable loop transitions and supports tool policy/executor, reflector, reviewer, and fallback callables. The next useful runtime maturity step is to make the `generating` phase carry a controlled model-output envelope. This gives SDK and Harness consumers a stable seam for future real LLM adapters while keeping the current project boundary conservative.

## Goals / Non-Goals

**Goals:**

- Add an explicit `model_step` callable to the execution loop.
- Normalize model-step output into a compact dictionary with stable keys.
- Persist the latest model-step output in run metadata.
- Emit a stable `execution_loop_model_step_completed` event.
- Let reviewer callables read model output from run metadata.
- Reuse existing fallback/fail-closed handling for model-step exceptions.
- Keep the seam opt-in and side-effect-free unless the caller-provided callable does work.

**Non-Goals:**

- No real LLM provider integration.
- No provider client injection, streaming, async model calls, retry, token accounting, or default model routing.
- No default `/api/chat` behavior change.
- No new ToolRuntime, worker, sandbox, or database behavior.
- No frontend governance UI change in this slice.

## Decisions

1. Model step is a callable seam on `ExecutionLoopController`, not a provider abstraction.

   Rationale: the project needs a stable runtime contract before binding a specific LLM provider. A callable keeps the test surface deterministic and allows future adapters to wrap provider calls behind the same contract.

   Alternative considered: integrate `ModelProviderRegistry` directly. Rejected because it would mix provider selection, real network/model behavior, and execution-loop contract design in one slice.

2. Model output is normalized as compact evidence.

   Rationale: governance and tests need stable fields without raw provider payloads. The output should include text, summary, model name, finish reason, usage, and metadata, but must exclude clients, streams, and callables.

   Alternative considered: store the raw callable result. Rejected because future provider outputs may contain unsafe or oversized runtime objects.

3. Model-step exceptions reuse the existing fallback handler path.

   Rationale: reviewer/fallback behavior is already established. Reusing `_handle_exception(...)` keeps model-step failure semantics consistent with reviewer failures.

   Alternative considered: introduce model-specific fallback events. Rejected for now because it creates another parallel failure contract before the generic loop failure path is insufficient.

4. Facade and SDK only pass through explicitly supplied model_step.

   Rationale: default behavior must remain stable. This slice makes the seam consumable without changing any existing chat or SDK runs.

## Risks / Trade-offs

- [Risk] The callable name may be mistaken for real LLM readiness. -> Mitigation: specs and docs state that no provider or default chat behavior is implied.
- [Risk] Sanitization may remove useful provider diagnostics later. -> Mitigation: preserve compact metadata and add richer diagnostics only through a future explicit provider/model adapter change.
- [Risk] Existing loop ordering could be disrupted. -> Mitigation: insert model_step after the generating state/status event and before tool policy/executor, leaving existing tool/reviewer/fallback ordering intact.

## Migration Plan

No migration is required. Existing callers do not pass `model_step`, so behavior stays unchanged. Rollback is removal of the optional parameter and related event/metadata handling.

## Open Questions

None for this slice. Real LLM provider routing, streaming, token accounting, and model degradation policy remain future OpenSpec changes.
