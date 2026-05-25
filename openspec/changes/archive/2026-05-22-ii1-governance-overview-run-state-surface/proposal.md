## Why

当前 `governance_overview.run` 还是一个很薄的壳，`child_merge_intent / child_merge_entities / child_merge_conclusion` 仍然主要由前端组合自 `childExecutorMergedSemantics.parentStateSurface`。

这会让 parent overview 的真源分散在两个位置：

- backend 的 profile contract
- frontend 的专题 read model 组合逻辑

下一步更合理的是把最稳定的运行上下文下沉进后端 `governance_overview.run`，让 Runtime Surface 的 parent overview 直接消费后端真源。

## What Changes

- `runtime-profile` 以及 `RuntimeSurfaceService.get_runtime_profile(...)` 接受显式 run scope 输入
- `governance_overview.run` 由后端统一构建，并包含最小 child merge state surface
- Runtime Surface 前端改为优先消费 `governance_overview.run`，不再从 child merged semantics 专题卡片里反向拼装 parent overview

## Impact

- `backend/services/runtime_surface_service.py`
- `backend/routers/health.py`
- `backend/schemas_runtime_surface.py`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `tests/agent_framework/test_runtime_surface_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
