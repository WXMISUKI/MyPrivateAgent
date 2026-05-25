## Why

当前 Embedded SDK recovery 已具备 durable posture、checkpoint/cursor、operation evidence 与 Runtime Surface read model，但仍缺少企业生产级恢复的三类关键 contract：worker ownership、失败重试恢复、恢复审计增强。先把这三类后续能力写成 OpenSpec 规格，可以避免后续实现时边做边定义。

收口对象：后续 recovery hardening 的规格边界。

非目标：本变更只生成规格文件，不实现 worker lease、不新增 retry executor、不改数据库结构、不改前端展示、不改变现有 SDK/Runtime Surface 输出。

## What Changes

- 新增 `runtime-worker-ownership-contract` 规格，定义 worker lease / ownership / fencing token / heartbeat / handoff 的生产级边界。
- 新增 `recovery-retry-protocol` 规格，定义恢复失败重试、退避、幂等、终止条件与 fail-closed 行为。
- 新增 `recovery-audit-hardening` 规格，定义恢复审计增强、Runtime Surface 汇总、trace/audit 关联与证据保留边界。
- 明确三者都必须复用既有 recovery operation evidence，不得重新发明平行恢复状态。

## Capabilities

### New Capabilities

- `runtime-worker-ownership-contract`: runtime worker ownership / lease / heartbeat / fencing token contract.
- `recovery-retry-protocol`: retryable recovery attempt contract with backoff, idempotency, and terminal fail-closed states.
- `recovery-audit-hardening`: governance-grade audit/read-model requirements for recovery operation evidence.

### Modified Capabilities

- `durable-recovery-operation-contract`: future hardening contracts must extend or consume existing recovery operation evidence instead of replacing it.
- `runtime-surface-recovery-operation-read-model`: future audit hardening must continue to use Runtime Surface read model as the read-side entry.

## Impact

- Affected specs only: OpenSpec change specs under `openspec/changes/define-recovery-hardening-contracts/specs/`.
- Affected future code paths: `backend/agent_framework/recovery_operations.py`, `backend/agent_framework/sdk.py`, `backend/services/runtime_surface_builders.py`, future worker/lease store modules.
- Affected docs later: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
