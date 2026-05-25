## Why

Embedded SDK approval lifecycle 已经具备正式事件：`approval_resolved`、`approval_replayed`、`approval_ignored`，并且 recovery fail-closed 路径也会输出 `recovery_failed_closed`。这些事件目前主要停留在 SDK event stream、runtime contract smoke 与 quality gate 证据里。

下一步需要把 SDK approval lifecycle 以受控方式接入平台治理 trace，让运行时审批的 accepted / replayed / ignored / recovery-blocked 状态可以进入 Governance Timeline，而不是只能从 SDK 内部事件或 smoke artifact 间接观察。

## What Changes

- Define an SDK approval lifecycle trace adapter contract.
- Add an opt-in, fail-open recorder path for Embedded SDK approval lifecycle events.
- Map compact SDK approval/recovery events into platform runtime trace entries without copying executable continuation internals.
- Preserve current SDK event stream semantics and approval immutability rules.
- Add focused tests proving trace write success, dedupe behavior, and recorder failure isolation.
- Update architecture, roadmap, and test manual after implementation.

## Non-Goals

- Do not write every SDK event to Governance Timeline.
- Do not change approval state machine semantics.
- Do not persist Python callables, provider clients, stream iterators, or executable continuation handlers.
- Do not make governance trace recording mandatory for SDK execution.
- Do not add a frontend panel in this first slice.
- Do not route ordinary main chat approval events through this adapter unless they are explicitly using the Embedded SDK path.

## Capabilities

### New Capabilities

- `sdk-approval-lifecycle-trace-adapter`: Defines how selected Embedded SDK approval lifecycle events can be recorded into platform runtime trace/audit as compact, opt-in governance evidence.

### Modified Capabilities

- `runtime-recovery-approval-kernel`: Clarifies that approval replay/ignored/recovery-blocked evidence may be mirrored to governance trace but must not change approval immutability or recovery reason semantics.

## Impact

- Backend SDK: `backend/agent_framework/sdk.py`
- Governance adapter/service: likely `backend/services/sdk_approval_timeline_service.py` or an equivalent focused helper.
- Trace service: consume existing `RunTraceService` seam without changing its public contract.
- Tests: focused SDK and new adapter tests under `tests/agent_framework/`.
- Docs/specs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, `docs/test_manual.md`, new OpenSpec capability.

## Validation

- OpenSpec strict validation for this change.
- Focused backend tests for SDK approval lifecycle trace recording.
- Existing Embedded SDK tests should continue to pass.

