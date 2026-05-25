## Why

Recovery operation evidence、worker ownership evidence、retry evidence 都已经有了最小 contract，但治理消费方仍需要自己遍历 operation history 才能回答“最近恢复状态是什么、失败集中在哪里、是否出现 retry/terminal/ownership 信号”。这会让 Runtime Surface、Governance Timeline 和后续 quality gate 重复实现同一套归纳逻辑。

本变更收口对象：`run_recovery` read model 的最小 recovery audit summary。它只做 read-side aggregation，不写 governance trace，不改变 SDK recovery 执行路径，也不把 audit summary 当成执行授权来源。

## What Changes

- 在 `RuntimeRecoveryContractBuilder` 中新增 recovery audit summary builder。
- `run_recovery` 输出新增 `recovery_audit_summary`。
- summary 统计 latest status / latest entrypoint / latest reason / operation counts / retry counts / ownership status / terminal status。
- 补 focused tests，证明 summary 从 compact operation history 派生，且不会暴露 executable payload。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `recovery-audit-hardening`: 从规格推进到 Runtime Surface read model 的最小 audit summary。
- `runtime-surface-recovery-operation-read-model`: `run_recovery` 增加 recovery audit summary。

## Impact

- Affected code: `backend/services/runtime_surface_builders.py`。
- Affected tests: `tests/agent_framework/test_runtime_surface_service.py` 或新增 focused builder tests。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
