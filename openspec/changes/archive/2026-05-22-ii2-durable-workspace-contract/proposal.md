## Why

Phase II 下一步需要把 `EmbeddedRunWorkspaceStore` 从“能保存快照和 continuation descriptor”推进到更正式的 durable workspace contract。当前 `describe_backend()` 只表达 backend 类型、是否 durable 和 fallback 状态，还没有机器可读地说明哪些状态属于 durable workspace，哪些仍是 in-process runtime state。

这会影响后续 checkpoint / resume cursor / cross-process recovery 的判断，也容易让调用方把当前 Python callable、stream cursor 这类临时状态误解为可持久化状态。

## 收口对象

- `EmbeddedRunWorkspaceStore.describe_backend()`
- `InMemoryEmbeddedRunWorkspaceStore`
- `SQLAlchemyEmbeddedRunWorkspaceStore`
- Runtime Surface 中透出的 `workspace_backend`

## What Changes

- 为 workspace backend description 增加 `state_contract`。
- 明确 durable state kinds：run snapshot、events、approval snapshot、tool continuation descriptor、loop continuation descriptor、artifact ref、child executor output。
- 明确 runtime-only state kinds：executable continuation callable、current Python function binding、temporary stream cursor、in-process event iterator。
- 不改变现有存储方法，不引入数据库迁移。

## 非目标

- 不实现完整 checkpoint loader。
- 不新增表结构。
- 不把 callable 或 stream cursor 持久化。
- 不接外部 graph runtime。

## Verification

```powershell
conda run -n myenv python -m unittest tests.agent_framework.test_embedded_workspace_store tests.agent_framework.test_runtime_surface_service -v
```
