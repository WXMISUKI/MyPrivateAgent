# Design: Embedded SDK End-to-End Integration Smoke Test

## Context

The Embedded SDK has two disconnected execution paths:
1. **Production path** (`/api/chat`): `SimplifiedOrchestrator` → `AgentHarness` → `model.astream()` — works end-to-end but bypasses `ExecutionLoopController`
2. **SDK path** (`execute_run`): `ExecutionLoopController` → `model_step` callable — governance-complete but never validated with real LLM

This change creates a smoke test that validates the SDK path works end-to-end, using a mock provider for deterministic tests and optionally a real provider for live validation.

## Goals

1. Create a deterministic integration test that exercises the full SDK loop with a mock provider.
2. Create a live smoke test script that exercises the full SDK loop with a real provider (Doubao/Ollama).
3. Validate that model output, tool execution, reviewer, and governance events are all captured correctly.
4. Provide a reference example for domain projects.

## Non-Goals

1. No streaming. The SDK path is synchronous for this slice.
2. No persistence/recovery. The smoke test uses in-memory state.
3. No changes to existing files (except docs).
4. No replacement of the production chat path.

## Key Decisions

### Decision 1: Two-layer test strategy

- **Layer 1 (deterministic)**: `test_sdk_e2e_integration.py` uses a mock provider and mock tool executor. Runs in CI, no network required. Validates the full loop structure.
- **Layer 2 (live)**: `sdk_e2e_smoke.py` uses the real `build_provider_model_step()` and `ToolRuntimeService`. Requires a running LLM provider. Validates real inference.

### Decision 2: Use AgentHarnessFacade as the entry point

The smoke test uses `AgentHarnessFacade.execute()` (not raw `EmbeddedAgentRuntimeSDK.execute_run()`) because:
- It's the developer-facing entry point
- It exercises the full stack including `model_name` auto-build
- It's what domain projects would use

### Decision 3: Register a simple test tool

The smoke test registers a simple tool (e.g., `get_current_time`) via `facade.register_tool()` to validate the `tool_executor` → `ToolRuntimeService` path. This is minimal but proves the tool execution seam works.

### Decision 4: Capture governance events as primary assertion

The main assertion is not "did the model say the right thing" (that's unpredictable) but "did the governance trace capture everything." We assert:
- `execution_loop_model_step_completed` event exists
- `execution_loop_step` events cover all states
- `execution_loop_done` event exists
- `metadata.execution_model_step` has text and model_name
- If tool was called: `tool_result` event exists

## Risks

| Risk | Mitigation |
|------|-----------|
| Real LLM call may fail (network, API key) | Layer 1 (mock) always passes; Layer 2 (live) is optional |
| LLM output is non-deterministic | Assert on structure, not content |
| Tool execution may behave differently in SDK path | Use simple tool (`get_current_time`) with predictable output |

## Migration

None required. This adds test infrastructure only.
