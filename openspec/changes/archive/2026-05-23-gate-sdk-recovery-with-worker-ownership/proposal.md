## Why

Worker ownership 目前已经有 in-memory lease/fencing seam，recovery operation 也能携带 ownership evidence，但 SDK 恢复入口仍不会消费该 seam。下一步需要让恢复入口在显式配置 ownership store 时先做 ownership validation，确保 stale fencing、过期 lease 或 lease mismatch 不会继续执行恢复。

本变更收口对象：Embedded SDK recovery gate 的 opt-in ownership validation。默认未配置 ownership store 时保持现有 `worker_ownership.implemented=false` 行为；配置后，在 registry-backed recovery operation 记录前校验 lease/fencing，失败时 fail-closed 并记录 blocked operation evidence。

非目标：不实现 SQL lease store、不做自动 claim、不改变默认 SDK 构造、不实现 distributed lock、不做 retry execution、不新增前端展示。

## What Changes

- `EmbeddedAgentRuntimeSDK` 支持可选 `worker_ownership_store`。
- 新增内部 ownership gate helper，根据 `worker_ownership` evidence 校验 active lease/fencing。
- `_record_recovery_operation(...)` 支持传入 `worker_ownership` evidence，并把校验后的 evidence 写入 operation record。
- registry-backed `submit_approval.approved` 与 `resume_run.continue_loop` 恢复路径在显式传入 ownership evidence 时执行 gate。
- 补 focused tests 覆盖 valid ownership、stale fencing fail-closed、默认无 ownership store 兼容。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `runtime-worker-ownership-contract`: ownership loss fail-closed 从 seam 推进到 SDK recovery gate 的 opt-in 实现。
- `durable-recovery-operation-contract`: blocked/recovered operation record 可携带 ownership gate evidence。

## Impact

- Affected code: `backend/agent_framework/sdk.py`。
- Affected tests: `tests/agent_framework/test_embedded_runtime_sdk.py` 或新增 focused SDK ownership gate tests。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
