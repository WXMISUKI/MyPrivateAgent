## Why

Phase II 的后端主线需要从治理台展示继续回到 Runtime Core 收口。当前 `EmbeddedAgentRuntimeSDK` 已经具备 approval replay/ignored、continuation descriptor、recovery probe、Runtime Surface recovery read model 和 quality gate checks，但这些能力仍分散在 SDK、Runtime Surface 和 smoke 脚本里。

下一步需要把 **approval lifecycle + recovery coordination** 提升为正式 kernel contract，让 `submit_approval()`、`resume_run()`、`probe_run_recovery()` 和 `get_run_recovery()` 对“现在还能不能恢复执行”使用同一套 machine-readable reason。

## 收口对象

- `EmbeddedAgentRuntimeSDK`
- `ApprovalEngineService`
- `RuntimeSurfaceService.get_run_recovery(...)`
- `runtime_contract_smoke.py`
- Runtime contract / roadmap / manual verification docs

## What Changes

- 固化 resolved approval 的 lifecycle contract：同决策重复提交为 `replayed`，反向提交为 `ignored`，都不能反改审批状态或重复执行 continuation。
- 将 recovery entrypoints 中 approval-gated 状态统一暴露为 stable `recovery_reason`，避免只有 UI/debug 语义的 `blocked_reason`。
- 将 smoke gate 从“能看到 approval replay/ignored 样本”升级为“能证明 approval lifecycle 与 recovery gate 对齐”。
- 保持当前自研 harness-style runtime core 路线；外部框架只作为参考，不进入主 chat 执行链。

## 非目标

- 不接入 LangGraph / OpenHands / Goose / Aider 作为主 runtime。
- 不新增数据库迁移。
- 不实现完整 child executor 或 sandbox runtime。
- 不改前端治理台布局。
- 不改变现有 API 字段名，只补充更稳定的 machine-readable reason。

## Impact

- Backend contract:
  - `runtime.recovery_entrypoints`
  - `approval_submission`
  - `runtime_contract_smoke` checks
- Tests:
  - `tests/agent_framework/test_approval_engine_service.py`
  - `tests/agent_framework/test_embedded_runtime_sdk.py`
  - `tests/agent_framework/test_runtime_surface_service.py`
  - `tests/agent_framework/test_runtime_contract_smoke.py`
- Docs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/test_manual.md`

## Verification

Run focused backend tests with the existing conda env:

```powershell
conda run -n myenv python -m unittest tests.agent_framework.test_approval_engine_service tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_runtime_contract_smoke tests.agent_framework.test_runtime_contract_gate_service tests.agent_framework.test_health_router -v
```
