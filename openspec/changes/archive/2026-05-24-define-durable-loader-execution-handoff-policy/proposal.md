## Why

DurableRecoveryLoader can now classify descriptor lifecycle evidence and produce registry-backed recovery candidates, but production recovery remains blocked because loader execution handoff policy is still missing. The next safe slice is to define how a read-only loader candidate may be handed to a future executor without executing it by default.

Without a handoff policy, future retry scheduler, worker ownership auto-claim, or cross-process recovery work could over-read `loader.status = ready` as an execution authorization.

## What Changes

- Add a `durable-loader-execution-handoff-policy` capability.
- Define a compact handoff policy contract and decision envelope.
- Expose handoff evidence on DurableRecoveryLoader candidates.
- Add runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot coverage for handoff policy evidence.
- Mark `loader_execution_handoff_policy` ready in the durable workspace production recovery gate while preserving other blocked sections.

## Capabilities

### New Capabilities

- `durable-loader-execution-handoff-policy`: Defines the explicit handoff policy between DurableRecoveryLoader and a future recovery executor.

### Modified Capabilities

- `durable-recovery-loader`: Loader candidates include handoff policy evidence.
- `durable-workspace-production-recovery-gate`: Handoff policy can be ready independently from worker ownership, audit, rollout, registry policy, and checkpoint/cursor gate.
- `embedded-sdk-persistence-interface`: Persistence posture exposes the updated production recovery gate.
- `embedded-sdk-recovery-protocol`: Recovery probes distinguish loader readiness, handoff policy readiness, and execution authorization.

## Impact

- 受影响后端 contract：`DurableRecoveryLoader`, `persistence_interface.production_recovery_gate`, runtime contract smoke summary。
- 受影响质量门禁：Quality Gate / Runtime Contract Gate / Snapshot 新增 `loader_execution_handoff_coverage.handoff_smoke`。
- 文档真源：`openspec/specs/*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不实现恢复执行器、不启动后台恢复、不反序列化 callable、不默认启用 production cross-process recovery。
