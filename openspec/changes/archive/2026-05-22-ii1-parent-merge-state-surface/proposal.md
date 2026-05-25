## Why

当前 `child_executor_merged_semantics` 已经有 dedicated read model 和 sectioned contract，但它还主要停留在 child output 专题消费面里。

下一步更值钱的不是继续增加字段，而是让 parent merge 结果进入更明确的 parent state surface，至少让 Runtime Surface 的 parent overview 能直接看到：

- 当前 child merge 意图
- 当前 parent merge 的主要 section 结果
- 最新 parent merge 结论

## What Changes

- 为 child merged semantics 增加最小 `parent_state_surface` 概览
- 在 Runtime Surface 的 parent/governance overview 中接入这层状态
- 保持 child output workspace 的详细展示不变

## Impact

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
