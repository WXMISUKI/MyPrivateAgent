## Why

Child executor dispatch result handoff can now explain compact backend output, but retry-related evidence is still just a raw `retryable` flag. We need a side-effect-free retry audit policy so governance can distinguish retryable failure evidence from actual retry scheduling or production worker enablement.

收口对象：child executor dispatch result retry audit policy after result handoff.

非目标：不调度 retry，不启动 worker，不实现 backoff clock，不执行 parent merge，不改变 dispatcher 默认 disabled 行为。

## What Changes

- Add a `child_executor_dispatch_result_retry_audit_policy` contract.
- Attach retry audit policy evidence to `child_executor_dispatch_result_handoff`.
- Cover retryable failure, terminal failure, and ready success/no-retry states in runtime smoke and quality gate.
- Sync Runtime Contract Gate, Snapshot guard, docs, and OpenSpec canonical specs.

## Capabilities

### New Capabilities
- `child-executor-dispatch-result-retry-audit-policy`: Defines machine-readable retry audit evidence for child executor dispatch result handoff without executing retries.

### Modified Capabilities
- `child-executor-dispatch-result-handoff`: Result handoff must preserve nested retry audit policy evidence.

## Impact

- Affected backend code:
  - `backend/agent_framework/child_executor_dispatcher.py`
  - `backend/agent_framework/__init__.py`
  - runtime smoke / quality gate / runtime contract gate / snapshot services
- Affected tests:
  - `tests/agent_framework/test_child_executor_dispatcher.py`
  - runtime contract smoke, quality gate report, runtime contract gate, snapshot, health router tests
- Affected docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - OpenSpec child executor dispatch result handoff / retry audit policy specs
- No API endpoint, frontend UI, database migration, worker loop, retry scheduler, or sandbox runtime is introduced.
