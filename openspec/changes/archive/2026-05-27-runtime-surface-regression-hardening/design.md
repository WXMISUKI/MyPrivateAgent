# Design

## Diagnosis Boundary

本 change 以现有失败测试为主反馈环，不新增大规模测试。先逐个运行失败用例，确认症状稳定，再读取对应测试和实现代码，定位导致 contract 退化的最小原因。

## Expected Fix Direction

1. `test_runtime_surface_uses_default_runtime_factory_for_sdk_reader`
   - 确认 Runtime Surface 的 SDK reader 是否绕过了 injected/default runtime factory。
   - 修复后，SDK reader 应通过同一 runtime factory 创建 SDK，避免测试和生产路径分叉。

2. `test_update_embedded_runtime_bootstrap_can_apply_workspace_store_mode`
   - 当前 `_validate_embedded_runtime_bootstrap_recovery` 对 mock 或非 mapping contract 调用 `dict(...)` 报错。
   - 修复后，validation 应对非 mapping contract fail-closed，而不是抛出 TypeError。

3. `test_update_runtime_profile_can_apply_embedded_workspace_store_mode`
   - 与 bootstrap update 共用 root cause，修复 validation 后应同时恢复。

4. `test_runtime_surface_can_return_child_executor_replay_and_summary`
   - 确认 child executor replay read model 的执行状态来源，避免已执行记录被前置 gate 状态覆盖成 `blocked`。

## Contract Principles

- Runtime Surface 只读 contract 不应因某个内部 mock/adapter contract 形状异常而整体报错。
- Replay/read model 应优先呈现真实执行记录状态，不应被 side-effect-free preflight 或 promotion gate 状态覆盖。
- SDK reader、Facade、Runtime Surface 应共享同一 runtime factory seam。
