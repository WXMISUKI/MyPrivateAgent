## Why

Runtime Surface 已经完成 profile shell、runtime core、provider catalog 等边界拆分，但 Embedded SDK / Harness 相关 read-model 仍分散在 profile assembler、service 方法和通用 builders 中。现在需要把这部分收口成独立 builder 边界，作为 Phase II Runtime Surface assembler closure 的最小高价值切片。

收口对象：`embedded_runtime_factory`、`embedded_runtime_bootstrap`、`default_runtime_recovery`、`run_recovery` 以及 governance overview 中消费的 recovery projection。该 change 只整理 read-model assembly，不改变 SDK 执行、恢复行为或 provider/domain-agent 调用策略。

## What Changes

- 新增 Embedded SDK Runtime Surface read-model assembler/builder 边界，集中承接 Embedded SDK / Harness 相关 contract 组装。
- 将 Runtime Surface profile assembly 和 dedicated bootstrap/run recovery service entrypoints 改为通过该 builder 读取现有合同。
- 保持现有外部 contract shape 不变，包括 Runtime Profile 顶层字段、bootstrap endpoint payload、run recovery payload 和 governance overview recovery projection。
- 补充 focused regression 测试，证明重构后 Runtime Surface Embedded SDK/Harness 相关字段仍稳定。
- 同步 runtime contract 文档和下一阶段路线归档说明。

非目标：

- 不改变 `EmbeddedAgentRuntimeSDK`、`AgentHarnessFacade`、Execution Loop、ToolRuntime、provider model-step adapter 或 domain-agent execution 行为。
- 不启用默认 `/api/chat` grounding、GraphRAG、source binding automation 或 final answer policy。
- 不引入 worker lease、后台自动恢复、分布式 executor、数据库迁移或新的 provider execution chain。
- 不调整前端治理台展示和 API 路由 contract。

## Capabilities

### New Capabilities
- `runtime-surface-embedded-sdk-assembler`: Defines the dedicated Runtime Surface read-model builder boundary for Embedded SDK / Harness contracts.

### Modified Capabilities
- `runtime-surface-contract-assembler`: Adds the requirement that Embedded SDK / Harness read-model assembly is delegated through the dedicated builder while preserving Runtime Surface contract shape.

## Impact

- Affected backend code:
  - `backend/services/runtime_surface_profile_assembler.py`
  - `backend/services/runtime_surface_service.py`
  - new builder module under `backend/services/`
  - focused tests in `tests/agent_framework/test_runtime_surface_service.py`
- Affected contracts:
  - Runtime Profile top-level `embedded_runtime_factory`
  - Runtime Profile top-level `embedded_runtime_bootstrap`
  - Runtime Profile top-level `default_runtime_recovery`
  - Runtime Profile top-level `run_recovery`
  - `governance_overview.run_recovery`
  - `governance_overview.default_runtime_recovery`
  - `governance_overview.recovery_alignment_summary`
- Affected docs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- No new external dependencies, API routes, database tables, provider calls, or frontend consumption changes.
