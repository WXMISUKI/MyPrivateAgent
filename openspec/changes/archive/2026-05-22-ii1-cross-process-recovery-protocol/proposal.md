## Why

`EmbeddedAgentRuntimeSDK` 现在已经具备 `workspace_store` seam，并且能把 persisted continuation descriptor 与 in-process executable continuation 明确区分开，但“能不能恢复、为什么不能恢复、恢复失败后如何可观测”还没有正式协议。现在继续推进 II-1，最值钱的不是再补存储，而是把 cross-process recovery 从隐含行为提升成正式 contract。

## What Changes

- 收口对象：
  - `tool_approval_continuation` 与 `loop_continuation` 的 cross-process recovery protocol
  - recovery probe / recovery attempt / fail-closed result contract
  - recovery 诊断在 SDK metadata、event stream、workspace descriptor 中的统一表达
- 新增能力：
  - 为 persisted continuation descriptor 增加正式 recovery status / reason / attempted_at 语义
  - 为 `resume_run(..., continue_loop=True)` 增加标准化 recovery gate 与 fail-closed 结果
  - 为 SDK 增加 recovery probe seam，先判断“是否可恢复”，再决定是否真正恢复
- 修改内容：
  - 明确 route 无关、前端无关，这一刀只落 Embedded SDK / Harness / Runtime Contract 文档
  - focused tests 从“descriptor 已持久化”扩到“descriptor 已持久化但不可恢复时的标准行为”
- 非目标：
  - 不实现真实 child executor
  - 不引入多进程 / 多实例协调器
  - 不把 persisted descriptor 直接提升成可执行 continuation
  - 不推进数据库迁移或默认强制 durable backend

## Capabilities

### New Capabilities
- `embedded-sdk-recovery-protocol`: 规范 Embedded SDK continuation 的 recovery probe、recovery result、fail-closed 行为与可观测事件。

### Modified Capabilities
- `query-run-read-model`: 无

## Impact

- **Backend**
  - `backend/agent_framework/sdk.py`
  - `backend/agent_framework/continuations.py`
  - `backend/agent_framework/persistence.py`
  - `backend/agent_framework/adapters.py`
  - `backend/agent_framework/harness.py`
- **Tests**
  - `tests/agent_framework/test_embedded_runtime_sdk.py`
  - `tests/agent_framework/test_agent_harness_facade.py`
  - `tests/agent_framework/test_embedded_workspace_store.py`
- **Documentation**
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/change/2026-05-18-phase-ii-embedded-sdk-persistence-recovery.md` 或等效阶段记录
