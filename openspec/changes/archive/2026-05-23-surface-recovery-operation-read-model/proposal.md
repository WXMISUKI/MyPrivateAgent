## Why

上一刀已经让 Embedded SDK 记录 durable recovery operation evidence，但消费方仍需要知道应该从哪里读取这份证据。企业生产级 Agent 平台应把恢复操作审计提升为 Runtime Surface 的正式 read model，而不是让治理台、健康检查或垂域项目从 SDK metadata / event samples 自行反推。

收口对象：Runtime Surface `run_recovery` read model 中的 recovery operation evidence。

非目标：本变更不新增前端展示、不改 worker lease、不实现跨实例执行所有权、不扩展 Runtime Contract Gate smoke 汇总。

## What Changes

- `probe_run_recovery()` 返回 latest recovery operation 与 bounded operation history。
- `RuntimeRecoveryContractBuilder.build_run_recovery_contract()` 将 recovery operation evidence 归一化为稳定字段。
- `RuntimeSurfaceService.get_run_recovery()` 和 profile 内嵌 `run_recovery` 自动透出该 read model。
- 更新 focused tests、OpenSpec canonical spec 与架构/测试文档。

## Capabilities

### New Capabilities

- `runtime-surface-recovery-operation-read-model`: 定义 Runtime Surface 如何暴露 SDK recovery operation evidence。

### Modified Capabilities

- `durable-recovery-operation-contract`: 明确 recovery operation evidence 必须能通过 `run_recovery` read model 被治理消费方读取。

## Impact

- Affected backend contract: `backend/agent_framework/sdk.py`、`backend/services/runtime_surface_builders.py`、`RuntimeSurfaceService.get_run_recovery()` 输出。
- Affected frontend consumption points: Runtime Surface / Governance Timeline 后续可直接读取 `run_recovery.latest_recovery_operation`；本切片不改 Vue。
- Docs truth sources: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
- Dependencies: 不新增第三方依赖。
