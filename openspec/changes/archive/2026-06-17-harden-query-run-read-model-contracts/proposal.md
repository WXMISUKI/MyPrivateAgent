## Why

`main_chat_query_detail`、`main_chat_query_history`、`recent_queries` 和 `run_recovery` 已经有实现，但其读模型边界仍分散在 Runtime Surface service、通用 builders 和前端消费点之间。现在需要把这组 Query/Run read model 继续硬化，避免后续 channel 扩展时再把语义推回前端推导。

收口对象：`main_chat_query_detail`、`main_chat_query_history`、`recent_queries`、`run_recovery` 及其在 `RuntimeSurfaceService`、`RuntimeSurfaceProfileAssembler`、Governance Timeline 和 Runtime Surface 面板中的消费方式。该 change 只做读模型收口，不改变默认 chat 行为或其他 channel 的能力边界。

## What Changes

- 强化 `main_chat_query_detail` 和 `main_chat_query_history` 的契约分工，确保 detail 与 history 分层清晰。
- 继续保持 `recent_queries` 作为轻量摘要列表，而不是主历史承载面。
- 保持 `run_recovery` 作为 Recovery Operation 读模型的正式入口，不把可执行恢复细节泄漏到治理视图。
- 将 Runtime Surface 与 Governance Timeline 对 query read model 的解释规则进一步收口为共享 contract interpretation。
- 补充 focused regression tests，确保 query/run 读模型和 recovery read model 的对外字段稳定。

非目标：

- 不推广到 `subagent_lane`、`external_adapter` 或其他 channel 的完整 history/workspace。
- 不改变 SDK 执行、provider 调用、worker lease、默认 `/api/chat` grounding 或 Query Control 事件采集行为。
- 不引入数据库迁移、schema 重构或新的前端大改。

## Capabilities

### New Capabilities
- `harden-query-run-read-model-contracts`: Hardens the existing query/run read-model boundary and shared interpretation rules.

### Modified Capabilities
- `query-run-read-model`: Clarifies the separation between query detail, history, recent summaries, and shared interpretation.
- `query-run-read-model-hardening`: Tightens the dedicated history endpoint and pagination-friendly contract boundary.
- `runtime-surface-recovery-operation-read-model`: Keeps `run_recovery` as the compact recovery operation evidence contract and clarifies its non-executable boundary.

## Impact

- Affected backend code:
  - `backend/services/runtime_surface_service.py`
  - `backend/services/runtime_surface_builders.py`
  - `backend/services/runtime_surface_embedded_sdk_builder.py` only if recovery builder delegation needs alignment
- Affected tests:
  - `tests/agent_framework/test_runtime_surface_service.py`
- Affected frontend consumers:
  - `RuntimeSurfacePanel`
  - `GovernanceTimelinePanel`
- Affected docs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- No new external dependencies or API surface expansion beyond the existing read models.
