## Why

当前仓库已经同时暴露 `POST /api/coze-workflows/{workflow_id}/invoke` 与 `POST /api/capabilities/{capability_id}/invoke`，但前者仍直接调用 workflow registry service，而不是统一走 capability runtime 生产调用链。这会让 Coze 工作流对外暴露时出现“入口存在但合同与失败语义未完全收口”的问题，不利于后续把 workflow 当作稳定接口提供给其他项目使用。

## What Changes

- 收口对象：把 `POST /api/coze-workflows/{workflow_id}/invoke` 统一改为通过 capability runtime 调用 `coze.workflow.<workflow_id>`，与 `POST /api/capabilities/{capability_id}/invoke` 共享同一生产入口和 envelope。
- 对 `coze-workflows` router 增加统一的 workflow-to-capability 解析与 fail-closed 处理，避免 workflow route 直接绕过 capability runtime。
- 补 focused backend tests，覆盖 workflow route 与 capability route 的合同一致性、未知 workflow 的 fail-closed 行为，以及 blocked workflow 的稳定错误语义。
- 同步更新 runtime contract / integration 文档，明确 workflow API 是 capability runtime 的别名入口，而不是第二条执行链。

非目标：
- 不重写 `CozeWorkflowRegistryService` 的具体执行器。
- 不新增鉴权系统、审批系统或 workflow 级 policy engine。
- 不扩展前端 Workflow Lab 或新的调试 UI。

## Capabilities

### New Capabilities
- `<none>`: None.

### Modified Capabilities
- `coze-workflow-invocation-api-hardening`: 将 workflow invoke route 收口到 capability runtime 统一生产调用链，并统一错误 envelope 与 fail-closed 语义。

## Impact

- 后端路由：
  - `backend/routers/coze_workflows.py`
  - `backend/routers/capabilities.py`
- 后端 runtime / registry：
  - `backend/capability_runtime/service.py`
  - `backend/services/coze_workflow_registry_service.py`
- 测试：
  - `backend/tests/coze_workflow_registry_test.py`
  - `tests/agent_framework/test_capabilities_router.py`
- 文档真源：
  - `docs/architecture/runtime_contracts.md`
  - 视情况补一份 `docs/integration/` 验收记录
