# Design: Embedded SDK Provider Model-Step Adapter

## Context

The execution loop's `model_step` seam is a pure callable contract. It does not call any LLM by itself. The codebase has a working but unspec'd `ModelProviderRegistry` + `ModelRouter` stack with two concrete backends (Doubao/Volcengine Ark and Ollama). No code currently bridges the provider registry to the `model_step` callable signature.

## Goals

1. Provide a factory function that wraps `ModelProviderRegistry` resolution into a `ModelStepCallable`.
2. The callable extracts `model_name` from `AgentRunContext`, resolves a LangChain model via the registry, invokes it synchronously, and returns an `ExecutionModelStepResult`.
3. Keep the adapter thin — it delegates model resolution to the existing registry and response normalization to `ExecutionModelStepResult`.
4. Make the adapter opt-in and side-effect-free until the caller passes it to `execute_run()`.

## Non-Goals

1. No streaming. The `model_step` callable is synchronous; streaming remains in the existing `/api/chat` path.
2. No tool-call loops. Tool execution stays with the `tool_executor` hook.
3. No token accounting, rate limiting, or retry. These are future concerns.
4. No model degradation policy. The `fallback_handler` hook owns degradation.
5. No changes to the existing chat path or default behavior.
6. No new provider backends.

## Key Decisions

### Decision 1: Factory function, not class

The adapter is a `build_provider_model_step(model_name, *, provider=None)` factory that returns a closure. Alternative of creating a `ProviderModelStep` class was rejected because the callable contract is already defined as `Callable[[AgentRunContext], ...]` and a closure is simpler.

### Decision 2: Sync invocation via `asyncio.run()`

The existing `ModelProvider.get_model()` returns a LangChain model instance. LangChain models support both `ainvoke()` (async) and `invoke()` (sync). The adapter will use `invoke()` for simplicity. If the caller is already in an async context, they should provide their own async model_step callable instead.

### Decision 3: Message construction from run_context

The adapter needs messages to call the model. It will construct a minimal message list from `run_context`:
- System message from `run_context.metadata.get("system_prompt")` (if present)
- User message from `run_context.metadata.get("user_message")` or `run_context.metadata.get("input")`

This is intentionally minimal. Richer message construction (history, tool results) belongs to the orchestrator layer, not the adapter.

### Decision 4: Provider resolution fallback

If `provider` is not explicitly passed, the adapter uses `get_model_provider()` (the existing `ModelRouterProviderAdapter` singleton). If the model is not available, the callable raises an exception, which the execution loop routes through the existing fallback/fail-closed path.

### Decision 5: No changes to existing files

The adapter is a new file `provider_model_step.py`. It imports from `providers.py`, `runtime.py`, and `execution_loop.py` but does not modify them. The facade may optionally accept a `model_name` string and auto-build a model_step, but this is a convenience wrapper, not a contract change.

## Risks

| Risk | Mitigation |
|------|-----------|
| Sync `invoke()` blocks the event loop if called from async context | Document that the adapter is for sync use; async callers should provide their own callable |
| Message construction is minimal | This is intentional; richer construction belongs to the orchestrator |
| Provider unavailable at call time | Exception routes through fallback/fail-closed, consistent with existing semantics |

## Migration

None required. This is a new opt-in adapter. Rollback is simply not using it.

## Open Questions

None for this slice.
