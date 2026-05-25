## Why

当前我们已经把 continuation recovery、binding catalog 和 child merge contract 收成了较稳定的底座，但 `delegate_run(...)` 进入真实 child executor 之前，仍缺一个可独立消费的 preflight contract 来回答“现在能不能升格、卡在哪、下一步该做什么”。
如果不先收口这一层，后续 child executor 很容易继续以 ad hoc metadata 方式扩展，恢复协议、权限门禁和 worker backend 选择也会再次分散到不同模块。

## What Changes

- 新增 child executor preflight 正式 contract，统一表达当前 child execution 是否可 promotion、卡点和推荐动作。
- 将 `executor_binding_status / executor_binding_blockers / recommended_next_step` 从内部评估结果提升为可稳定消费的运行时读模型。
- 明确 preflight 的收口对象：`delegate_run(...)`、child output merge、continuation binding、worker runtime backend、promotion gate。
- 保持当前 `delegate_run(...)` 仍然只是 relationship seam，preflight 仅提供升格判断，不直接启动真实 child executor。
- 让 Runtime Surface / Facade / SDK 对“是否可进入真实 child executor”共享同一套 contract，而不是各自推导。

## Capabilities

### New Capabilities
- `child-executor-preflight-contract`: 统一 child executor preflight 评估、contract 暴露与前端消费。

### Modified Capabilities
- （无）

## Impact

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/continuation_registry.py`
- `backend/services/runtime_surface_service.py`
- `backend/routers/health.py`
- `backend/schemas_runtime_surface.py`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/ChildExecutorOutputWorkspace.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `tests/agent_framework/test_runtime_surface_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
