## Why

`RuntimeSurfaceService.get_runtime_profile()` 已经同时承担模型/提供方聚合、主视图 read model 组装、恢复态拼装和治理摘要编排，文件和职责都在持续膨胀。现在继续向后端加能力时，如果不先收紧它的内部边界，后续每一刀都会更难维护，也更难单测。

## What Changes

- 把 `get_runtime_profile()` 中最臃肿的组装逻辑抽到独立 assembler/builder，减少 `RuntimeSurfaceService` 的编排负担。
- 保持 `runtime_profile` 对外返回结构稳定，外部 API 不因这次重整而变化。
- 将模型/提供方聚合、main chat read model 组装、run recovery 组装、child executor summary 组装等逻辑按职责拆分到更清晰的内部边界。
- 允许少量字段整理，但不改变现有治理读模型语义和前端消费契约。
- 同步补充 focused tests 与文档说明，确保 assembler 抽离后仍可作为新的后端真源演进。

## Capabilities

### New Capabilities
- `runtime-surface-contract-assembler`: 将 `RuntimeSurfaceService.get_runtime_profile()` 的主要组装逻辑抽离成独立 assembler/builder 边界，同时保持外部 contract 稳定。

### Modified Capabilities
- `runtime-surface`: `get_runtime_profile()` 的内部实现边界将被重整，但对外 contract 不变。

## Impact

- Backend: `backend/services/runtime_surface_service.py`, `backend/services/runtime_surface_builders.py`, 以及相关 focused tests。
- Docs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- OpenSpec: 新增 `runtime-surface-contract-assembler` 能力规格，作为后续实现与测试的约束真源。
