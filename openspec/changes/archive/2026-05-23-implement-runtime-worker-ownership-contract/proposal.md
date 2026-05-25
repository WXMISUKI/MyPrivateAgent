## Why

Recovery operation evidence 已能说明一次恢复尝试发生了什么，但 `worker_ownership.implemented` 仍固定为 `false`。要继续推进企业生产级恢复能力，下一步应先建立 worker ownership 的最小 contract 和 adapter seam，让后续 retry / audit 能依赖同一套 lease/fencing 证据。

收口对象：runtime worker ownership contract 的最小实现，包括 in-memory lease store、claim/heartbeat/validate 语义，以及 recovery operation evidence 的 ownership payload 支持。

非目标：本变更不实现 SQL lease store、不把 ownership 强制接入所有恢复入口、不做分布式锁、不实现 retry protocol、不新增前端展示。

## What Changes

- 新增 `backend/agent_framework/worker_ownership.py`，提供 worker ownership contract、lease record、in-memory ownership store。
- 支持 `claim_run(...)`、`heartbeat(...)`、`validate_ownership(...)` 三个最小操作。
- `recovery_operations.build_recovery_operation_record(...)` 支持传入 ownership evidence；未传入时保持现有 `implemented=false` payload。
- 补 focused unit tests，证明 claim、heartbeat、stale fencing、expired lease、operation payload 均符合规格。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `runtime-worker-ownership-contract`: 从规格推进到最小 in-memory adapter seam。
- `durable-recovery-operation-contract`: recovery operation record 可携带 implemented worker ownership evidence。

## Impact

- Affected code: `backend/agent_framework/worker_ownership.py`、`backend/agent_framework/recovery_operations.py`。
- Affected tests: 新增 focused worker ownership tests，必要时补 recovery operation payload assertions。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
