## Why

Stage 1 runtime-plane work already has `simple_agent` and `tool_agent`; the highest-value remaining slice is proving that high-risk tool intent can stop at a normalized approval interrupt instead of being executed locally. This closes the minimum runtime-plane MVP loop needed before later governance bridge or managed-runtime pilots.

收口对象：`approval_agent` adapter slice, limited to normalized approval-pending envelopes for high-risk tool calls.

非目标：do not create production approvals, do not resume approved execution, do not modify default `/api/chat`, do not add a scheduler, checkpoint engine, sandbox, or managed runtime integration.

## What Changes

- Add a minimal `ApprovalAgentAdapter` under `backend/runtime_plane/adapters/`.
- Detect high-risk or approval-required tool calls from the existing local Agent graph result and translate them into:
  - `ExecutionEvent(stage="approval", type="approval_required")`
  - `ExecutionResult(status="approval_pending")`
  - compact approval metadata that contains only request/tool/risk summaries.
- Ensure high-risk tools are not executed in this slice; the adapter stops before tool invocation.
- Add focused tests for blocked health, approval-pending envelope, and no high-risk handler execution.
- Add runtime-plane stage review docs for the approval-agent slice.

## Capabilities

### New Capabilities

- `runtime-plane-approval-agent-adapter`: Defines the minimum approval-agent adapter behavior for normalizing high-risk tool intent into a side-effect-free approval interrupt envelope.

### Modified Capabilities

- `runtime-plane-integration-strategy`: Records that Stage 1 now includes the approval-agent slice as the third MVP vertical slice, while keeping real approval execution out of scope.

## Impact

Affected code:

- `backend/runtime_plane/adapters/approval_agent.py`
- `backend/runtime_plane/adapters/__init__.py`
- `backend/runtime_plane/__init__.py`
- `backend/tests/runtime_plane/test_approval_agent_adapter.py`

Affected docs/specs:

- `openspec/changes/add-runtime-plane-approval-agent-adapter/`
- `docs/architecture/runtime_plane_integration_strategy.md`
- `docs/roadmap/next_phase_hardening.md`
- `docs/roadmap/runtime_plane_stage_1_approval_agent_review.md`
