## Why

我们已经有 child executor preflight、binding catalog、recovery protocol 和 parent-facing merge/state surfaces，但 `delegate_run(...)` 何时能从 relationship seam 升格为真实 child executor，仍缺一个稳定、可消费的 promotion gate 真源。
如果继续只在边界卡片里解释升格条件，后续 worker runtime、route/binding 和治理视图会再次分裂出多套判断口径。

## What Changes

- 新增 child executor promotion gate 正式 contract，用于描述当前 child run 是否允许进入真实执行阶段。
- 将 preflight 的 readiness 结果进一步收束为 gate 结果，统一输出 allowed / blocked、failure reason、executor path 与 blockers。
- 把升格条件固定为后端真源，而不是让前端、Facade 或 call site 自己拼装判断。
- 保持 `delegate_run(...)` 在 gate 未通过前仍是 relationship seam；promotion gate 只负责“可不可以升格”，不直接执行 child executor。
- 把 child executor 的升格判断与 binding catalog、workspace backend、merge semantics、recovery boundary 保持一致。

## Capabilities

### New Capabilities
- `child-executor-promotion-gate`: 统一 child executor promotion gate contract、backend 暴露和前端消费。

### Modified Capabilities
- （无）

## Impact

- `backend/agent_framework/sdk.py`
- `backend/agent_framework/harness.py`
- `backend/services/runtime_surface_service.py`
- `backend/routers/health.py`
- `backend/schemas_runtime_surface.py`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/ChildExecutorOutputWorkspace.vue`
- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `tests/agent_framework/test_runtime_surface_service.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
