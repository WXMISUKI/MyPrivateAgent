## Why

Worker ownership has a useful lease/fencing seam today: in-memory preview store, SQLAlchemy durable adapter, strict/prefer-fallback store mode, heartbeat, fencing validation, runtime smoke coverage, and SDK opt-in recovery enforcement. That is enough for controlled recovery attempts, but it is not yet enough to treat worker ownership as production-default execution authority.

The missing decision point is a machine-readable production gate that says whether default cross-instance ownership enforcement may be enabled. Without this gate, future recovery retry, cross-process recovery, and child executor work can accidentally over-read "SQL row lease exists" as "production distributed ownership is ready."

## What Changes

- Add a `worker-ownership-production-gate` capability that defines production enablement requirements.
- Clarify that SQL row lease/fencing remains a durable adapter posture, not a vendor-specific distributed lock by itself.
- Require production gate evidence for vendor lock semantics, renewal supervision, rollout/migration checklist, recovery-entry auto-claim policy, stale fencing fail-closed, and audit evidence.
- Keep default worker ownership production enablement disabled until the gate is ready.

## Capabilities

### New Capabilities

- `worker-ownership-production-gate`: Defines the fail-closed gate for enabling worker ownership as a production-default runtime authority.

### Modified Capabilities

- `worker-ownership-operations`: Extends operational readiness with production gate semantics.
- `runtime-worker-ownership-contract`: Exposes the production gate through the runtime worker ownership contract.

## Impact

- 受影响后端 contract：`worker_ownership.operational_readiness`, default runtime factory worker ownership contract, runtime contract smoke ownership check.
- 受影响质量门禁：后续 implementation 必须让 quality gate summary 可读取 production gate blocked/ready 证据。
- 文档真源：`openspec/specs/worker-ownership-*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
- 非目标：本 change 不实现 vendor 专用锁、不启动后台续租 loop、不默认开启 recovery entry auto-claim、不改变现有 SDK opt-in recovery gate。
