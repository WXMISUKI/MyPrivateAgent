## Why

当前 child executor merge 已经具备最小 intent-aware 行为，但还有两个明显缺口：

- `intent_label` 仍然只是分散在实现中的字符串约定，还不是稳定 contract
- parent merged semantics 虽然已经有 dedicated read model，但仍然是一块扁平对象，不利于后续 parent 侧按 section 消费

如果继续在这个基础上直接推进真实 child executor，后续很容易在不同消费面里重复解释 intent 和 merge 结果。

## What Changes

- 把 child executor intent taxonomy 固化为稳定枚举 contract
- 为 parent merged semantics 增加最小 section 结构
- 保持现有 `latest_merged_semantics` / summary / Runtime Surface 兼容
- 让后续 parent 视图可以直接消费 sectioned merge result，而不是继续从扁平字段拼装

## Impact

- `backend/agent_framework/sdk.py`
- `backend/services/runtime_surface_service.py`
- `backend/routers/health.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_runtime_surface_service.py`
- `tests/agent_framework/test_health_router.py`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/ChildExecutorOutputWorkspace.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
