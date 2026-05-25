## Why

Child executor preflight and promotion gate can already say whether a delegated run stays relationship-only, but they do not yet expose a dedicated execution-prerequisites contract that answers what is still missing before a real child executor may be wired in. This slice closes that gap before any executor implementation work, keeping the production default fail-closed and auditable.

## What Changes

- Add a backend `child_executor_execution_prerequisites` contract derived from existing preflight, binding, merge, worker backend, and promotion gate truth sources.
- Surface the prerequisites contract through SDK gate output and Runtime Surface promotion gate payload so consumers do not recompute readiness from raw metadata.
- Add runtime contract smoke and quality gate summary evidence for prerequisite coverage.
- Sync runtime contract docs and roadmap with the new boundary.

收口对象：真实 child executor 执行前置条件的机器可读 contract。

非目标：

- 不启动真实 child executor。
- 不引入数据库迁移、worker 调度器、沙箱执行或跨实例 child executor lease。
- 不改变 `delegate_run(...)` 当前 relationship seam 默认行为。

## Capabilities

### New Capabilities
- `child-executor-execution-prerequisites`: Defines the machine-readable prerequisites required before promotion from relationship seam to real child executor execution.

### Modified Capabilities
- `child-executor-promotion-gate`: Promotion gate must expose execution prerequisite evidence and remain blocked until prerequisites are satisfied.

## Impact

- Backend SDK contract builders in `backend/agent_framework/sdk.py`.
- Runtime Surface assembly and schema in `backend/services/runtime_surface_service.py` and `backend/schemas_runtime_surface.py`.
- Runtime contract smoke, quality gate report, Runtime Contract Gate, and snapshot guard.
- Docs truth sources: `docs/architecture/runtime_contracts.md` and `docs/roadmap/next_phase_hardening.md`.
