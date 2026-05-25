## Why

Recovery retry has moved beyond pure evidence: the runtime now has compact retry evidence, recovery operation audit history, and an explicit opt-in scheduler seam. It still must not become default automatic retry until production readiness gates for durability, worker ownership, idempotency, backoff, and audit are explicit.

## What Changes

- Add a production scheduler gate capability that defines when automatic recovery retry may be enabled.
- Clarify that the existing scheduler remains opt-in and non-default until the production gate is ready.
- Extend retry protocol requirements to cover durable scheduling state, idempotency/dedupe, backoff clock, terminal decisions, worker ownership, and audit fail-open/fail-closed boundaries.
- Update roadmap/architecture notes to distinguish opt-in scheduler seam from production automatic retry.

## Capabilities

### New Capabilities

- `recovery-retry-production-scheduler-gate`: Defines readiness requirements before automatic recovery retry can be enabled by default or used by background runtime scheduling.

### Modified Capabilities

- `recovery-retry-scheduler`: Clarify the transition from explicit opt-in scheduler seam to production automatic scheduler.
- `recovery-retry-protocol`: Add durable scheduling and audit/idempotency constraints required for production retry execution.

## Impact

- 收口对象：Recovery retry 自动调度的生产启用门槛。
- 受影响后端 contract：`recovery_operation_contract.retry_policy`, `RecoveryRetryScheduler`, `run_recovery.recovery_audit_summary`, worker ownership recovery gate, recovery audit trace writer.
- 受影响前端消费点：无直接 UI 变更；后续仍消费 recovery audit/read-model 摘要。
- 文档真源：`openspec/specs/recovery-retry-*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不实现后台自动 retry loop、不默认开启 scheduler、不新增进程内轮询器、不绕过 worker ownership、不复制第二套 retry event model。
