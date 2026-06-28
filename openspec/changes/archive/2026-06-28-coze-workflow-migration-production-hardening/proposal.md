## Why

我们已经把单个 Coze 工作流迁移、只读注册和 Workflow Lab 回放跑通了，但要让后续多人持续迁移并真正对外投产，仍然缺少一套统一的收口契约：哪些 Coze 节点映射为本地 runtime capability，哪些必须明确暴露 blocker，以及哪些工作流可以以稳定 API 形式被其他项目调用。现在做这一步最合适，因为它能把“单个样例成功”提升为“可复制的迁移生产线”。

## What Changes

- 标准化 Coze 工作流的依赖映射结果，把节点统一归类为 `runtime_capability`、`provider_backed`、`artifact_input`、`explicit_blocker` 四类，避免后续迁移时依赖语义漂移。
- 为已推广的工作流补齐稳定调用入口的契约收口，使工作流可以作为 capability API 对外暴露，而不是停留在单个迁移样例或临时路由。
- 保持 Workflow Lab 作为只读验证面，用于检查 registry、dependency mapping、acceptance example 和 replay diff，不把它变成第二条执行链。
- 明确把模型 provider registry、模型列表、baseurl/apikey 管理放到后续变更，不混入本次迁移收口。

## Capabilities

### New Capabilities
- `coze-workflow-dependency-mapping-contract`: 定义 Coze 工作流节点到本地 runtime capability / provider / artifact / blocker 的映射规则、分类结果和 blocker 语义。
- `coze-workflow-invocation-api-hardening`: 定义已推广工作流的稳定调用入口、版本化 capability id、授权边界、trace 摘要和 fail-closed 行为。

### Modified Capabilities
- 

## Impact

- 后端：`backend/coze_workflows/` 下的 workflow manifest、dependency mapping 组装、invoke envelope、Workflow Lab 读取服务和相关路由。
- API：`GET /api/coze-workflows`、`GET /api/coze-workflows/{workflow_id}`、`GET /api/coze-workflows/{workflow_id}/readiness`、`GET /api/coze-workflows/{workflow_id}/capability`、`POST /api/coze-workflows/{workflow_id}/invoke`，以及统一 capability invoke 链路。
- 文档：`docs/guides/coze_migration_workflow_authoring.md`、`docs/guides/coze_workflow_lab_verification_runbook.md`、`docs/guides/capability_runtime_registry.md`、`docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`。
- 前端：`frontend-vue/src/views/WorkflowLabView.vue`、相关测试与侧边栏入口，保持只读验证和回放展示。
- 测试：后端聚焦测试、前端 Workflow Lab 测试、OpenSpec change 验证。
