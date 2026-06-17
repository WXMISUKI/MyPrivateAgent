# Proposal: Embedded SDK End-to-End Integration Smoke Test

## Background

The Embedded SDK has accumulated significant infrastructure:
- `ExecutionLoopController` with full state machine and 6 callable seams
- `build_provider_model_step()` adapter wrapping real LLM providers
- `ToolRuntimeService` for tool execution with policy/schema/retry
- Approval lifecycle with continuation recovery
- Governance trace, audit, and quality gate coverage

However, **no one has ever validated that these pieces work together with a real LLM call**. The SDK path (`execute_run` → `ExecutionLoopController` → `model_step` → `tool_executor`) has never been exercised end-to-end with actual model inference. All existing tests use mocks.

The `/api/chat` production path works (via `SimplifiedOrchestrator` → `AgentHarness` → `model.astream()`), but it is a completely separate execution engine from the SDK path. The two paths share provider infrastructure but have different execution loops, event formats, and governance surfaces.

## Purpose

Create a focused end-to-end integration smoke test that proves the Embedded SDK path works with a real LLM provider, covering the full loop:

```
AgentHarnessFacade.execute(model_name="doubao")
  → build_provider_model_step("doubao")
  → ExecutionLoopController
  → model.invoke() [real LLM]
  → tool_executor → ToolRuntimeService [real tool]
  → reviewer [governance gate]
  → governance trace [events captured]
```

This validates the architecture thesis: "you bring the framework, we bring the governance."

## Scope

- NEW: `backend/scripts/sdk_e2e_smoke.py` — end-to-end smoke test script
- NEW: `tests/agent_framework/test_sdk_e2e_integration.py` — deterministic integration tests with mock provider
- NEW: Canonical spec `embedded-sdk-e2e-integration-smoke`
- MODIFIED: Runtime contracts and roadmap docs

## Non-Goals

- No streaming support (model_step stays synchronous)
- No changes to the existing `/api/chat` production path
- No persistence/recovery changes
- No new provider backends
- No frontend changes
- No child executor changes

## Capabilities Affected

- NEW: `embedded-sdk-e2e-integration-smoke`

## Impact

- Backend: new smoke test script, new integration test, docs
- No external API, DB schema, frontend, or default behavior changes
