## Why

Worker ownership 已经有了最小 lease/fencing seam，但 recovery retry 仍只停留在 canonical spec。下一步应该先把 retry policy 与 retry attempt evidence 固定到 recovery operation contract 上，让后续失败重试恢复可以复用同一 operation evidence，而不是新增平行事件模型。

本变更收口对象：recovery retry 的最小 evidence contract，包括 retry policy 声明、retry payload compact 化、retryable/terminal reason 分类，以及 operation record 中的 retry evidence。

非目标：本变更不实现自动 retry scheduler、不在 SDK 恢复入口里循环执行重试、不做 backoff timer、不新增前端展示、不改变现有恢复成功/失败流程。

## What Changes

- `backend/agent_framework/recovery_operations.py` 新增 retry policy contract 与 retry payload compact helper。
- `build_recovery_operation_contract()` 暴露 `retry_policy`，声明当前 retry execution 未实现但 evidence contract 已可用。
- `build_recovery_operation_record(...)` 支持传入 compact `retry` evidence；未传入时保持无 retry payload，兼容现有 operation shape。
- 补 focused tests，证明 retry policy、retry payload、terminal retry reason、非可执行 payload 均符合规格。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `recovery-retry-protocol`: 从规格推进到最小 retry evidence contract。
- `durable-recovery-operation-contract`: recovery operation record 可携带 compact retry evidence。

## Impact

- Affected code: `backend/agent_framework/recovery_operations.py`。
- Affected tests: 新增 focused recovery retry protocol tests，并跑 SDK / Runtime Surface 回归。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
