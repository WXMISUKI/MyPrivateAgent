## Context

当前 Embedded SDK 已经有：

- persistence posture：`memory_preview / durable_ready / durable_degraded`
- `production_recovery_gate`：说明默认生产恢复何时可能被允许
- run-specific recovery probe：说明某个 run 是否可恢复
- worker ownership、loader handoff、audit readiness、registry/checkpoint policy 等 compact evidence

但还缺一层显式的 `authorization dry-run`。这会导致两个问题：

1. 调用方只能从多个 gate 手动推断“现在是否值得进入授权评审”。
2. 团队容易把已有 readiness 误解成生产默认恢复授权。

Stakeholders：

- Embedded SDK / Harness 调用方，需要机器可读的授权候选判断。
- Runtime Surface / Governance 消费方，需要稳定 read model，而不是手工拼接多个内部证据。
- 平台维护者，需要继续保持 fail-closed、opt-in、non-executable 的边界。

## Goals / Non-Goals

**Goals:**

- 新增 side-effect-free 的 `embedded_sdk_production_recovery_authorization` contract。
- 让该 contract 复用现有 `production_recovery_gate`、worker ownership enablement input、loader handoff、audit evidence。
- 通过 Runtime Surface 暴露默认恢复与 run 级恢复的授权摘要。
- 为 smoke / quality gate / snapshot 增加覆盖，避免 contract 漂移。

**Non-Goals:**

- 不执行恢复、不提交审批、不调用 worker ownership claim。
- 不新增后台自动恢复、retry scheduler、child executor dispatch。
- 不改默认 provider、chat 或 domain-agent 执行行为。
- 不新增数据库迁移、SQL 写路径或新的 durable backend。

## Decisions

### 1. 授权 contract 放在 persistence 层，而不是 SDK execute 路径

决定：
- 在 `backend/agent_framework/persistence.py` 增加授权 dry-run contract builder。

原因：
- 授权判断本质上是 persistence / recovery readiness 的上层解释，而不是执行循环行为。
- 这样可以直接复用 production recovery gate 与 worker ownership evidence，不把 execute path 再变复杂。

备选：
- 放进 `EmbeddedAgentRuntimeSDK`。
  - 放弃，因为这会让 SDK 执行路径承担更多治理拼装责任。

### 2. 授权 dry-run 必须显式依赖“授权输入源”

决定：
- 只有存在 caller-owned 的授权输入源，并且 gate / ownership / audit / handoff 证据 ready，dry-run 才能报告 `ready`。

原因：
- 这样能继续守住“readiness 不等于 authorization”的边界。
- 也能复用既有 `worker_ownership` 中的 enablement input source / runtime config consumer。

备选：
- 当 production gate ready 时自动认为 authorization ready。
  - 放弃，因为这会把 gate readiness 误读成授权来源。

### 3. Runtime Surface 只暴露 read model，不暴露执行开关

决定：
- 在 `EmbeddedSdkRuntimeSurfaceBuilder` 中暴露默认恢复和 run 恢复的授权摘要。

原因：
- 这符合当前 Runtime Surface assembler 的职责边界。
- 前端和治理消费者可以直接读取结果，不再自己拼多个 nested gate。

备选：
- 只更新文档，不更新 Runtime Surface。
  - 放弃，因为这样无法被真实调用方稳定消费。

### 4. 质量门禁必须覆盖授权 dry-run

决定：
- 在 `runtime_contract_smoke.py` 增加授权 dry-run check，并让 `quality_gate_report.py`、`RuntimeContractGateService`、snapshot 一起消费。

原因：
- 这是 runtime contract 变更，必须进入现有 gate 链。
- 否则授权 contract 只存在于实现，无法防止后续漂移。

备选：
- 只加单测，不进 quality gate。
  - 放弃，因为这条 contract 的价值就在于跨模块一致性。

## Risks / Trade-offs

- [Risk] 授权 contract 和 production gate 职责重叠，看起来重复。 -> Mitigation: 明确 gate 是默认启用边界，authorization 是显式评审候选 dry-run。
- [Risk] Runtime Surface contract 继续膨胀。 -> Mitigation: 只暴露 compact authorization summary，不透出执行 payload。
- [Risk] 团队把 `ready` 误解成“可以自动恢复”。 -> Mitigation: contract 字段显式保留 `will_execute = false`、`authorization_source`、`non_goals`。

## Migration Plan

1. 新增授权 dry-run contract builder，并先用 focused tests 固定行为。
2. 把该 contract 接入 persistence interface 和 Runtime Surface Embedded SDK builder。
3. 增加 smoke / quality gate / snapshot coverage。
4. 同步回写架构文档与 roadmap。

回滚策略：
- 如果授权 contract 设计不稳，优先移除 Runtime Surface 暴露并保留内部 builder，而不是改动现有 recovery gate 或 SDK execute 行为。

## Open Questions

- run-specific recovery 是否需要单独暴露 `authorization_source`，还是只保留 compact `authorization_summary` 即可。
- 后续进入真正 production authorization change 时，是否复用同一 contract 名称继续扩展，还是再新增 execution authorization layer。
