## Why

`main_chat_query_detail` 和 `main_chat_query_history` 已经作为独立 read model 存在，但当前契约只表达了“能读什么”，还没有明确“这是什么层级、来自哪个通道、按什么身份标识”。这会让前端治理面板、审计和后续扩展继续依赖隐含约定，而不是直接消费自描述契约。

## What Changes

- 为 `main_chat_query_detail` 补充自描述元数据，明确其 read model 层级、来源通道与身份语义。
- 为 `main_chat_query_history` 补充同类元数据，并明确分页语义是 `page + cursor` 兼容演进，而不是临时列表拼装。
- 保持现有 detail/history 字段结构不变，只做向后兼容的契约增强。
- 同步更新文档真源与 focused tests，确保前后端对 contract 的理解一致。

## Capabilities

### New Capabilities
<!-- No new capability. This change modifies an existing read model capability only. -->

### Modified Capabilities
- `query-run-read-model`: 既有 `main_chat` query read model 契约需要补充 self-describing metadata，并收口 detail/history 的边界语义。

## Impact

- Backend: `backend/services/runtime_surface_builders.py`, `backend/services/runtime_surface_service.py`, `backend/services/runtime_contract_snapshot_service.py`。
- Tests: `tests/agent_framework/test_runtime_surface_service.py`, `tests/agent_framework/test_runtime_contract_snapshot_service.py`。
- Docs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, `openspec/specs/query-run-read-model/spec.md`。
- Frontend consumers: `RuntimeSurfacePanel`, `GovernanceTimelinePanel` 的 contract normalization 将更依赖显式元数据，而不是隐式判断。
