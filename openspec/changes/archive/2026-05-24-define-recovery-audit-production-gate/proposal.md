## Why

Durable workspace production recovery is still blocked by several production sections. Recovery audit is the smallest next section to close because the runtime already has compact recovery operation history, recovery audit summary, and an opt-in RecoveryAuditTimelineService.

Without a production audit gate, future worker ownership, retry scheduler, or cross-process recovery executor work could execute recovery without proving that operation history and trace correlation are available as governance evidence.

## What Changes

- Add a `recovery-audit-production-gate` capability.
- Add a compact recovery audit operation history readiness contract.
- Mark `recovery_audit_operation_history` ready in the durable workspace production recovery gate.
- Expose recovery audit production coverage through runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot.
- Keep audit evidence separate from execution authorization and worker lease validation.

## Capabilities

### New Capabilities

- `recovery-audit-production-gate`: Defines production readiness evidence for recovery operation history and optional audit trace correlation.

### Modified Capabilities

- `recovery-audit-hardening`: Clarifies production gate evidence for audit summary and trace writer readiness.
- `durable-workspace-production-recovery-gate`: Allows recovery audit operation history to be ready independently from worker ownership and rollout.
- `embedded-sdk-persistence-interface`: Persistence posture exposes the updated production recovery gate.
- `durable-recovery-operation-contract`: Operation contract exposes audit production readiness evidence.

## Impact

- 受影响后端 contract：`recovery_operation_contract`, `persistence_interface.production_recovery_gate`, runtime contract smoke summary。
- 受影响质量门禁：新增 `recovery_audit_operation_history_coverage.audit_smoke`。
- 文档真源：`openspec/specs/*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不把 audit 当成执行授权、不启用默认跨进程恢复、不替代 worker ownership lease validation。
