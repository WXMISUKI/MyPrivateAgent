## Why

当前 Runtime Core 的核心对象已经基本具备，但 `query / run / child run / scheduler run / approval / artifact / trace / audit` 的语义仍分散在多个 service、前端视图和文档里。若不先收口术语与对象模型，后续 Query/Run Read Model、治理视图和新 adapter 接线都会继续放大命名漂移。

## What Changes

- **收口 Runtime Core 术语**
  - 明确 `query`、`run`、`child run`、`scheduler run`、`approval`、`artifact`、`trace`、`audit` 的正式语义与非语义边界。
  - 明确 `durable state` 与 `runtime state` 的分层。
  - 明确 `control plane` 与 `execution plane` 的责任边界。
- **统一高漂移对象的首要命名**
  - 固化 `child_run_id` 为 Runtime Core 正式术语。
  - 明确 `child_execution_id` 仅作为 scheduler / repository 兼容键。
  - 固化 `child_display_id` 作为前端展示层稳定标识。
- **同步治理与交付层的表述**
  - 统一 Runtime Surface、Governance Timeline、PlannerPanel、ChatView 中的相关术语。
  - 约束前端只能消费后端 contract，不再自行发明近义词。
- **文档真源同步**
  - 更新 `docs/architecture/runtime_contracts.md`
  - 更新 `docs/architecture/current_architecture.md`
  - 更新 `docs/change/2026-05-16-phase-g-agent-runtime-reference-alignment.md`
  - 必要时同步 `docs/roadmap/next_phase_hardening.md`

## Capabilities

### New Capabilities
- `runtime-core-terms-model`: Runtime Core 术语、对象模型与命名收口规范，定义 query/run/child run/scheduler run/approval/artifact/trace/audit 的稳定边界。

### Modified Capabilities
- `query-run-read-model`: 其语义依赖 Runtime Core 术语收口，本次变更会强化 query 与 run 的边界定义，但不改变 read model 的职责分工。

## Impact

- **Backend**
  - `backend/agent_framework/runtime.py`
  - `backend/agent_framework/events.py`
  - `backend/services/scheduler_runtime_entities.py`
  - `backend/services/scheduler_runtime_contract.py`
  - `backend/services/scheduler_runtime_store.py`
  - `backend/services/run_trace_service.py`
  - `backend/services/runtime_surface_service.py`
  - `backend/services/scheduler_service.py`
  - `backend/services/chat_service.py`
- **Frontend**
  - `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - `frontend-vue/src/components/PlannerPanel.vue`
  - `frontend-vue/src/views/ChatView.vue`
- **Documentation**
  - `docs/architecture/runtime_contracts.md`
  - `docs/architecture/current_architecture.md`
  - `docs/change/2026-05-16-phase-g-agent-runtime-reference-alignment.md`
  - `docs/roadmap/next_phase_hardening.md`

