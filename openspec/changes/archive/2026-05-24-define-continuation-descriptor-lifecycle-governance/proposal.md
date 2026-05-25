## Why

Durable workspace recovery now exposes persistence posture, checkpoint/resume cursor, registry-backed loader evidence, and fail-closed production recovery gates. The next blocker is continuation descriptor lifecycle governance: persisted descriptors need a compact, machine-readable lifecycle before they can participate in production cross-process recovery decisions.

Without lifecycle evidence, future loader handoff, worker ownership auto-claim, or retry scheduler work could over-read a persisted descriptor as safe simply because it exists and has a binding id.

## What Changes

- Add a `continuation-descriptor-lifecycle-governance` capability.
- Define descriptor lifecycle states: `created`, `bound`, `ready`, `stale`, `resolved`, and `unsafe`.
- Add compact lifecycle evidence to DurableRecoveryLoader candidates and fail-closed paths.
- Add runtime smoke / quality gate / Runtime Contract Gate / snapshot coverage for lifecycle evidence.
- Mark descriptor lifecycle governance as complete in the durable workspace production recovery gate while preserving other blocked sections.

## Capabilities

### New Capabilities

- `continuation-descriptor-lifecycle-governance`: Defines safe lifecycle state classification for persisted continuation descriptors.

### Modified Capabilities

- `durable-recovery-loader`: Loader evidence includes descriptor lifecycle summaries.
- `durable-workspace-production-recovery-gate`: Descriptor lifecycle governance can be ready independently from loader handoff or execution enablement.
- `embedded-sdk-recovery-protocol`: Recovery probes expose descriptor lifecycle evidence before production default recovery can advance.

## Impact

- 受影响后端 contract：`DurableRecoveryLoader`, `persistence_interface.production_recovery_gate`, runtime contract smoke summary.
- 受影响质量门禁：Quality Gate / Runtime Contract Gate / Snapshot 新增 `continuation_descriptor_lifecycle_coverage.lifecycle_smoke`。
- 文档真源：`openspec/specs/*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不执行跨进程恢复、不反序列化 callable、不新增后台 loader handoff、不默认启用 production recovery。
