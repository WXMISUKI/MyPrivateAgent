## Why

Durable recovery has moved beyond a preview seam: the runtime now exposes persistence posture, checkpoint, resume cursor, DurableRecoveryLoader, registry-backed reattach, recovery operation evidence, and smoke/quality gate coverage. It still must not be treated as fully production cross-process recovery until the default enablement gate for durable workspace state, descriptor lifecycle, registry binding, worker ownership, audit, and rollout is explicit.

Without a production recovery gate, future retry scheduler, recovery entry auto-claim, or child executor work could over-read `durable_ready` or a persisted descriptor as "safe to recover across processes."

## What Changes

- Add a `durable-workspace-production-recovery-gate` capability.
- Clarify that persistence posture remains a backend capability signal, not a single-run recovery authorization.
- Clarify that DurableRecoveryLoader remains a read-only candidate loader unless a production recovery gate is ready and explicitly enabled.
- Extend recovery protocol requirements with descriptor lifecycle and production cross-process recovery gate semantics.

## Capabilities

### New Capabilities

- `durable-workspace-production-recovery-gate`: Defines production readiness before cross-process recovery can be enabled by default.

### Modified Capabilities

- `embedded-sdk-persistence-interface`: Adds production gate evidence to persistence posture.
- `durable-recovery-loader`: Clarifies loader execution boundary under the production gate.
- `embedded-sdk-recovery-protocol`: Adds descriptor lifecycle and gate requirements for production cross-process recovery.

## Impact

- 受影响后端 contract：`persistence_interface`, `durable_recovery_loader_contract`, `default_recovery_expectation`, runtime contract smoke persistence/loader checks.
- 受影响质量门禁：Quality Gate / Runtime Contract Gate summary 需要能证明 production recovery gate blocked，而不是只看 durable loader ready。
- 文档真源：`openspec/specs/durable-*`, `openspec/specs/embedded-sdk-*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不实现跨进程恢复执行器、不反序列化 callable、不绕过 registry binding、不默认启用 recovery entry auto-execute。
