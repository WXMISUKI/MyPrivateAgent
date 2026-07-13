## Why

Embedded SDK 的 persistence / recovery readiness 已经收口，但“readiness 已具备”和“允许进入生产恢复授权评审”之间还缺一个明确、可读、fail-closed 的中间层。现在补这层最值钱，因为它能把现有 SDK 主干继续往可投产方向推进，又不会误把 readiness 证据当成默认自动恢复授权。

## What Changes

- 新增 `embedded-sdk-production-recovery-authorization` 能力，定义一个 side-effect-free 的生产恢复授权 dry-run contract。
- 在 Embedded SDK persistence interface 中暴露该授权 dry-run，明确它与 `production_recovery_gate`、run-specific probe、worker ownership evidence 的关系。
- 在 Runtime Surface Embedded SDK read model 中暴露默认恢复与 run 级恢复的授权摘要，供治理面和调用方读取。
- 为 runtime contract smoke、quality gate summary、Runtime Contract Gate 与 snapshot 增加对应 coverage，确保这条授权链不是只存在于代码内部。

收口对象：
- `Embedded SDK production recovery authorization` 只解释“是否具备进入显式授权评审的条件”，不执行恢复。
- `persistence_interface.production_recovery_gate` 继续作为默认生产恢复启用前的 fail-closed gate。
- `run_recovery` 与 `default_runtime_recovery` 继续保留 run-specific recovery probe 语义，不被授权 dry-run 取代。

非目标：
- 不启用默认后台自动恢复。
- 不启动 worker、retry scheduler 或 child executor。
- 不改变 `/api/chat`、provider、domain-agent 执行行为。
- 不新增数据库迁移或持久化后端改造。

## Capabilities

### New Capabilities
- `embedded-sdk-production-recovery-authorization`: 定义 Embedded SDK 生产恢复授权 dry-run contract，复用既有 readiness/gate evidence，但不执行恢复。

### Modified Capabilities
- `embedded-sdk-persistence-interface`: persistence interface 需要显式暴露生产恢复授权 dry-run，而不是只停留在 production recovery gate。
- `runtime-surface-embedded-sdk-assembler`: Runtime Surface 需要稳定暴露 Embedded SDK 授权读模型，而不是让前端或调用方从多个 gate 手工拼接。

## Impact

- 后端 contract：
  - `backend/agent_framework/persistence.py`
  - `backend/services/runtime_surface_embedded_sdk_builder.py`
  - `backend/services/runtime_surface_service.py`
  - `backend/scripts/runtime_contract_smoke.py`
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
  - `backend/services/runtime_contract_snapshot_service.py`
- 前端消费点：
  - 继续消费 `Runtime Surface` 的 embedded SDK / recovery read model，不新增直接执行入口。
- 文档真源：
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/change/phase-ii-exit-gate-assessment.md`
