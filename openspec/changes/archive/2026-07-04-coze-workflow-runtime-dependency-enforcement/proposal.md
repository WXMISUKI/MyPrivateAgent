## Why

随着更多 Coze 工作流迁移进来，当前的“能发现、能注册、能调用”还不够。我们需要在执行前把 `http.request`、文件输入、OCR、RAG、视觉模型和外部 provider 等依赖显式收口成一个统一的 fail-closed 门禁，否则团队会继续遇到“看起来已接入、实际一运行就缺依赖”的问题。

## What Changes

- 收口对象：把 Coze workflow 的 dependency mapping 变成 shared preflight contract，供 registry detail、Workflow Lab 和 workflow invoke 共用。
- 把 registry/detail 的 dependency mapping 与 invoke preflight 统一到同一个 dependency mapper，避免 lab、registry、invoke 三处各自推导。
- `POST /api/coze-workflows/{workflow_id}/invoke` 在执行前必须检查 dependency mapping blocker，遇到 `explicit_blocker` 或 provider-backed 依赖未就绪时 fail closed。
- 让 Workflow Lab 继续只读展示 dependency mapping，但改为消费同一份共享契约，不再各自拼装 blocker 语义。
- 同步更新文档与 focused tests，确保多人迁移时可直接依赖同一份 mapping contract。

非目标：
- 不引入数据库迁移。
- 不重写具体 workflow executor，比如 `hazardous_project_list_recognition` 的解析逻辑。
- 不新增鉴权系统、审批系统或新的调试前端。
- 不把 artifact_input 默认升级成执行阻断，仍以 schema / runtime reference 校验为准。

## Capabilities

### New Capabilities
- `<none>`: None.

### Modified Capabilities
- `coze-workflow-dependency-mapping-contract`: 将 dependency mapping 提升为 registry / lab / invoke 共享的 preflight read model，并明确 blocker 语义用于执行前检查。
- `coze-workflow-invocation-api-hardening`: 在 capability runtime 之外补上 dependency mapping preflight，fail closed 处理 unsupported / unresolved 依赖。

## Impact

- 后端服务：
  - `backend/services/coze_workflow_registry_service.py`
  - `backend/services/coze_workflow_lab_service.py`
  - 可能新增一个 shared dependency mapper helper module
- 后端路由：
  - `backend/routers/coze_workflows.py`
- 测试：
  - `backend/tests/coze_workflow_registry_test.py`
  - `backend/tests/coze_workflow_lab_test.py`
  - `tests/agent_framework/test_coze_workflows_router.py`
- 文档真源：
  - `docs/architecture/runtime_contracts.md`
  - 视需要补 `docs/integration/` 的上线验收记录
