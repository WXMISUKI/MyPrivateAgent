## Why

`query / run / child_run / approval / trace / audit` 的正式语义已经在文档和实现里出现，但不同规格、治理视图和说明文案仍存在局部表述漂移，容易让维护者把同一个对象当成不同概念。现在需要把这组核心术语收口成统一真源，避免后续 read model 和治理视图继续分叉。

## What Changes

- 收口 `query` 与 `run` 的正式边界，明确它们不是同一对象的不同叫法。
- 收口 `child_run_id`、`child_execution_id`、`child_display_id` 的主次关系，避免对外展示和后端兼容键继续混用。
- 收口 `approval`、`trace`、`audit` 的对象语义，避免把治理对象和执行证据混成一层。
- 收口治理视图里对 `query / run` 的解释方式，让 Runtime Surface、Governance Timeline 和 query read model 共享同一套术语解释。
- 收口 `query detail / query history / query workspace` 的边界叙述，避免把 read model 层和 workspace 层混成同一个概念。

## Capabilities

### Modified Capabilities

- `runtime-core-terms-model`: 统一 Runtime Core 术语定义，补足 query/run/child_run/approval/trace/audit 的正式边界。
- `query-run-read-model`: 对齐 query/run 读模型与治理视图术语，避免 contract 文案与 Runtime Core 定义漂移。
- `governance-view-unification`: 让 Runtime Surface 与 Governance Timeline 共享同一套 query/run 术语解释和 focus 语义。

## Impact

- 后端 runtime contract 文案与 snapshot 守护字段。
- `runtime_surface_service.py`、`runtime_contract_snapshot_service.py`、`query_control_*` 相关解释逻辑。
- `frontend-vue/src/services/governanceViewInterpretation.js` 以及 Runtime Surface / Governance Timeline 的共享解释入口。
- `docs/architecture/runtime_contracts.md`、`docs/architecture/current_architecture.md`、`docs/roadmap/next_phase_hardening.md`。
