# Proposal: Add Embedded SDK Provider Model-Step Adapter

## Background

The `add-embedded-sdk-model-step-contract` change completed an opt-in `model_step` callable seam on `ExecutionLoopController`. The seam accepts a `ModelStepCallable` that runs during the `generating` stage and normalizes output into compact `ExecutionModelStepResult` evidence.

However, the seam is purely abstract — no built-in callable exists that actually calls a real LLM. Vertical-agent projects must hand-author their own `model_step` function each time.

Meanwhile, the codebase already has a working `ModelProviderRegistry` + `ModelRouter` + `ProviderBackend` stack (`providers.py`, `provider_backends.py`, `model_router.py`, `adapters.py`) with two concrete backends (Doubao/Volcengine Ark and Ollama). This infrastructure is unspec'd but functional.

## Purpose

Create a thin adapter function `build_provider_model_step()` that wraps the existing `ModelProviderRegistry` into a `ModelStepCallable`, enabling:

```python
model_step = build_provider_model_step(model_name="doubao")
result = sdk.execute_run(run_id, model_step=model_step)
```

This bridges the provider infrastructure to the execution loop without changing the existing chat path, introducing streaming, or modifying default behavior.

## Scope

- NEW: `build_provider_model_step()` factory function in `backend/agent_framework/provider_model_step.py`
- NEW: Canonical spec `embedded-sdk-provider-model-step-adapter` defining the adapter contract
- NEW: Focused backend tests for the adapter (provider resolution, successful call, provider unavailable, response normalization)
- MODIFIED: `agent-harness-facade-v1` delta spec — facade can accept a model name and auto-build a model_step
- MODIFIED: Runtime contracts and roadmap docs

## Non-Goals

- No streaming support (model_step is synchronous)
- No tool-call loops within model_step (tool execution stays with tool_executor)
- No token accounting, rate limiting, or retry policy
- No model degradation policy (that belongs to fallback_handler)
- No changes to the existing `/api/chat` production flow
- No new provider backends (only wraps existing registry)
- No frontend UI changes
- No changes to `ExecutionLoopController`, `EmbeddedAgentRuntimeSDK`, or `AgentHarnessFacade` signatures

## Capabilities Affected

- NEW: `embedded-sdk-provider-model-step-adapter`
- MODIFIED: `agent-harness-facade-v1`

## Impact

- Backend: new file `provider_model_step.py`, focused tests
- Docs: runtime contracts, roadmap
- No external API, DB schema, frontend, or default chat behavior changes
