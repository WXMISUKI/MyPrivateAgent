## Context

当前 Coze workflow 迁移链路已经具备：
- `backend/coze_workflows/<workflow_id>/workflow.yaml` 作为资产真源。
- `CozeWorkflowRegistryService` 负责 list/detail/readiness/capability metadata。
- `CapabilityRegistry + CapabilityRuntimeService` 已能把 ready workflow 暴露为 `coze.workflow.<workflow_id>` capability。
- `POST /api/capabilities/{capability_id}/invoke` 已是统一 capability runtime 入口。

但 `POST /api/coze-workflows/{workflow_id}/invoke` 仍直接调用 `registry_service.invoke_workflow(workflow_id, payload)`。这意味着 workflow route 与 capability route 虽然大体返回相近 envelope，但没有真正通过同一入口收口，后续如果 capability runtime 增加统一审计、ownership、policy、错误标准化，workflow route 可能再次漂移。

## Goals / Non-Goals

**Goals:**
- 让 `POST /api/coze-workflows/{workflow_id}/invoke` 委托 `CapabilityRuntimeService.invoke(capability_id, payload)`。
- 对 workflow route 保留 workflow-friendly 404 行为，但成功和失败 envelope 要与 capability runtime 返回一致。
- 用 focused tests 锁住“同一 workflow 从两个入口调用，合同 shape 一致”。
- 在文档中明确 workflow route 是 capability runtime 的别名入口，而不是第二条生产执行链。

**Non-Goals:**
- 不改变 workflow manifest 结构。
- 不改造具体 workflow executor，比如 `hazardous_project_list_recognition` 的实现细节。
- 不在本次引入真实 authorization 计算、审批写路径或新的 invoke policy evaluator。
- 不新增前端入口或 Workflow Lab 交互。

## Decisions

### Decision 1: Workflow route 通过 capability runtime 调用，而不是继续直接调用 registry service
- 选择：
  - 在 router 层先解析 workflow id -> capability id，再委托 `CapabilityRuntimeService.invoke(...)`。
- 原因：
  - 这是最小改动，同时满足“统一生产调用链”的 spec 意图。
  - 不需要改 CapabilityRuntimeService 的内部模型，也不需要替换 registry 的 invoker。
- 不选方案：
  - 让 `registry_service.invoke_workflow` 再反向调用 capability runtime。这个方向会把 registry 从 manifest/readiness contract 污染成 runtime coordinator，不利于职责边界。

### Decision 2: 未知 workflow 在 workflow route 保持 404，但已知 capability 的业务失败继续沿用 runtime envelope
- 选择：
  - `workflow_id` 无法解析时仍返回 `COZE_WORKFLOW_NOT_FOUND` + 404。
  - workflow 已存在但 blocked / invalid / execution failed 时，沿用 capability runtime 返回的 envelope。
- 原因：
  - 这保留了 workflow API 的可读性，同时不破坏统一生产 envelope。

### Decision 3: 优先在 backend focused tests 里锁合同一致性，不新增前端验收
- 选择：
  - 补 registry focused test 和 router focused test。
- 原因：
  - 这次变更纯属后端入口收口，前端不消费新的合同字段。
  - 先把“别名入口与主入口一致”锁住，比扩展 UI 更有价值。

## Risks / Trade-offs

- [Risk] workflow route 与 capability route 的 HTTP 状态码仍存在轻微差异
  → Mitigation：仅在 `workflow not found` 场景保留 workflow-specific 404；其它失败尽量复用 capability runtime envelope，并在 spec / docs 中明确。

- [Risk] router 侧 capability id 解析逻辑与 registry metadata 漂移
  → Mitigation：优先从 registry workflow detail 读取 `capability_id`，没有时再按 `coze.workflow.<workflow_id>` 回退。

- [Risk] 未来 capability runtime 增加更复杂 policy 后，workflow route 还需要同步
  → Mitigation：这次先把 route 委托点收口到 capability runtime，后续 policy 只需在 capability runtime 演进。

## Migration Plan

1. 修改 `backend/routers/coze_workflows.py`，把 invoke route 切到 capability runtime。
2. 补 focused tests，覆盖：
   - active workflow 从 workflow route 调用成功
   - workflow route 与 capability route envelope 关键字段一致
   - unknown workflow 返回 404
   - review / blocked workflow 维持 fail-closed
3. 更新 docs 真源，说明 workflow route 是 capability runtime alias。
4. 运行 focused tests 与 strict validate。

回滚策略：
- 如果新 route 出现兼容性问题，可回滚 router 层委托改动；registry service 与 capability definitions 不受影响。

## Open Questions

- 这次先不引入 capability runtime 层的统一 HTTP error mapping；后续若要把 400/404/503 统一抽象，可单独开 change。
