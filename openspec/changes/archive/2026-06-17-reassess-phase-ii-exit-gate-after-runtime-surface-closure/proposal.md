## Why

Phase II 初版 exit gate 评估停留在 2026-06-14，当时 Runtime Surface assembler、Governance Timeline slimming、SDK/domain-agent 执行闭环都还未完成近期收口。现在多个关键 change 已归档，需要重新评估 Phase II 是否应关闭、继续补最小 blocker，或进入 Phase III。

收口对象：`docs/change/phase-ii-exit-gate-assessment.md`、`docs/roadmap/next_phase_hardening.md` 中的 Phase II 收束标准、当前完成度、blockers、下一步 allowed action。该 change 只做 exit gate 复评与决策，不新增 runtime 行为。

## What Changes

- 更新 Phase II exit gate assessment，使其反映最近完成的 Runtime Surface Embedded SDK assembler、Query/Run read model hardening、Governance Timeline slimming、Embedded SDK/provider model-step/domain-agent SDK execution 等收口项。
- 明确 Phase II 当前结论：可关闭、不可关闭但只剩单一 blocker、或进入有限收束模式。
- 更新下一阶段建议，避免继续沿 provider evidence、query workspace、UI 细节无限拆分。
- 固定下一个最小 allowed implementation slice，作为后续阶段入口。

非目标：

- 不实现新的 SDK durable recovery、worker lease、retry scheduler、child executor 或 provider behavior。
- 不改变默认 `/api/chat`、GraphRAG、source binding、domain-agent answer policy 或 frontend UI。
- 不新增 provider onboarding 项，也不重新打开 channel query history/workspace 扩展。

## Capabilities

### New Capabilities
- `phase-ii-exit-gate-reassessment`: Defines how Phase II exit readiness is reassessed after Runtime Surface and Query/Run read-model closure work.

### Modified Capabilities
- `runtime-surface-contract-assembler`: Records Runtime Surface assembler closure as Phase II exit evidence.
- `query-run-read-model-hardening`: Records Query/Run read-model hardening as Phase II exit evidence.
- `embedded-sdk-recovery-acceptance-smoke`: Keeps Embedded SDK recovery acceptance as readiness evidence but not production recovery authorization.

## Impact

- Affected docs:
  - `docs/change/phase-ii-exit-gate-assessment.md`
  - `docs/roadmap/next_phase_hardening.md`
- Affected specs:
  - New `phase-ii-exit-gate-reassessment`
  - Existing Runtime Surface / Query-Run / Embedded SDK recovery readiness specs as evidence links
- Affected validation:
  - OpenSpec strict validation
  - Focused Runtime Surface / SDK tests if needed to confirm evidence is still readable
- No API, database, frontend UI, provider, SDK execution, or default chat behavior changes.
