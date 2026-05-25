## Why

The child executor execution prerequisites contract can now say which prerequisites are missing, but worker backend readiness still depends on caller-provided strings rather than a backend-owned capability registry. This slice introduces a small registry contract so the system can distinguish "backend name was supplied" from "backend is known and allowed as a child executor candidate" before any real executor dispatch is implemented.

## What Changes

- Add a read-only child executor backend registry contract with stable backend ids, readiness status, dispatch mode, and blockers.
- Use the registry when evaluating child executor preflight and execution prerequisites.
- Surface the registry through SDK contract and Runtime Surface so consumers can inspect backend availability without recomputing readiness.
- Add focused tests and docs for the new boundary.

收口对象：child executor worker backend capability registry 与 readiness evidence。

非目标：

- 不启动真实 child executor。
- 不实现 executor scheduling、sandbox、remote worker、queue、lease renewal 或 hard timeout。
- 不引入数据库迁移或外部服务依赖。
- 不改变默认 relationship-only 安全行为。

## Capabilities

### New Capabilities
- `child-executor-backend-registry`: Defines the machine-readable registry of worker backends that may satisfy child executor backend readiness.

### Modified Capabilities
- `child-executor-preflight-contract`: Worker backend readiness must be derived from a known backend registry entry, not only from a non-empty backend string.
- `child-executor-execution-prerequisites`: Execution prerequisites must include backend registry evidence when evaluating worker backend readiness.

## Impact

- Backend SDK contract builders in `backend/agent_framework/sdk.py`.
- Runtime Surface profile assembly and schema in `backend/services/runtime_surface_service.py` and `backend/schemas_runtime_surface.py`.
- Focused tests under `tests/agent_framework/`.
- Docs truth sources: `docs/architecture/runtime_contracts.md` and `docs/roadmap/next_phase_hardening.md`.
