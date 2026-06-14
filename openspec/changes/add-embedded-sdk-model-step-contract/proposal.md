## Why

The Embedded SDK execution loop now has controlled tool, reviewer, fallback, and recovery seams, but the `generating` stage still has no explicit model-step contract. Adding a small opt-in model step moves the runtime toward real agent execution without pulling in real LLM providers or changing default chat behavior.

收口对象：Embedded SDK / AgentHarnessFacade 的显式 `model_step` consumption seam，覆盖生成阶段输出、事件、metadata、reviewer/fallback 协同和安全 payload 边界。

非目标：不接真实 LLM、不接 provider client、不做 streaming、不改变默认 `/api/chat`、不新增 worker/sandbox/tool 行为、不做前端 UI。

## What Changes

- Add a new opt-in `model_step` callable contract for the Execution Loop `generating` stage.
- Normalize model step output into compact metadata and `execution_loop_model_step_completed` events.
- Route model step exceptions through existing fallback/fail-closed loop behavior.
- Pass `model_step` through `EmbeddedAgentRuntimeSDK.execute_run(...)` and `AgentHarnessFacade.execute(...)`.
- Ensure model step evidence excludes provider clients, active streams, raw SDK objects, and executable callables.
- Update specs, runtime docs, roadmap, and focused tests.

## Capabilities

### New Capabilities

- `embedded-sdk-model-step-contract`: Defines opt-in model step behavior, output shape, event semantics, fallback semantics, and non-goals.

### Modified Capabilities

- `embedded-sdk-execution-loop-reviewer-fallback`: Adds model-step interaction with reviewer and fallback contracts.
- `agent-harness-facade-v1`: Adds explicit facade pass-through for `model_step` without changing default run/execute behavior.

## Impact

- Backend: `backend/agent_framework/execution_loop.py`, `backend/agent_framework/sdk.py`, and `backend/agent_framework/harness.py`.
- Tests: focused backend tests for model-step success, reviewer consumption, fallback handled, fail-closed, and payload sanitization.
- Docs/specs: canonical OpenSpec specs plus `docs/architecture/runtime_contracts.md` and `docs/roadmap/next_phase_hardening.md`.
- No external API, database schema, frontend, provider, or default chat behavior changes.
