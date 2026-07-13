# Embedded SDK Production Recovery Authorization Slice Review

> 日期：2026-07-13
> 范围：`add-embedded-sdk-production-recovery-authorization-slice`
> 状态：已完成实现与聚焦验证，待后续归档

## 1. 本次切片做了什么

本次只完成一个最小受控切片：

- 在 `backend/agent_framework/persistence.py` 新增 side-effect-free `embedded_sdk_production_recovery_authorization` dry-run contract。
- 复用既有 `production_recovery_gate`、worker ownership enablement input/runtime config consumer、loader handoff、recovery audit evidence。
- 在 Runtime Surface 的 `default_runtime_recovery` 与 `run_recovery` 中新增 compact authorization summary。
- 把该 contract 接入 runtime smoke、quality gate summary、runtime contract gate 和 snapshot。

## 2. 明确没有做什么

本次明确没有进入以下范围：

- 没有执行 recovery。
- 没有提交 approval。
- 没有 claim worker ownership。
- 没有启动 background worker。
- 没有启动 retry scheduler。
- 没有默认开启 production recovery。
- 没有改 `/api/chat`、provider、domain-agent 或 child executor 的默认执行路径。

## 3. 证据

本次聚焦验证已覆盖：

- `tests/agent_framework/test_embedded_workspace_store.py`
- `tests/agent_framework/test_runtime_surface_service.py`
- `tests/agent_framework/test_runtime_contract_smoke.py`
- `tests/agent_framework/test_quality_gate_report.py`
- `tests/agent_framework/test_runtime_contract_gate_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`

关键验证点：

- blocked 样本必须保留 `authorization_request_source` / `worker_ownership_enablement_input` blocker evidence。
- ready 样本必须仍保持 `will_execute = false`。
- Runtime Surface 读取到的是 compact summary，不是执行开关。
- quality gate / gate service / snapshot 缺失新 coverage 时会 fail closed。

## 4. 当前判断

这个切片已经达到“可继续作为 Phase III 受控基线”的程度。

也就是说：

- 它已经足够作为后续真正 production authorization change 的上游 dry-run contract。
- 它还不应该被误用成 production automation 的替代品。

## 5. 下一步允许动作

允许：

1. 基于当前 dry-run contract 继续推进下一最小 `Embedded SDK / Execution Loop hardening` 切片。
2. 围绕 explicit authorization review、runtime config binding 或 controlled execution seam 再开新 change。

不允许：

1. 直接把 `ready` 解释成“可以自动恢复”。
2. 在当前 change 内顺手放开 worker、scheduler 或 background recovery。
3. 用当前 dry-run contract 替代 run-specific recoverability probe。
