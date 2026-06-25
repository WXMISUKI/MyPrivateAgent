# Phase II Exit Gate Assessment

> 日期：2026-06-17
> 状态：复评完成
> 来源：`openspec/changes/reassess-phase-ii-exit-gate-after-runtime-surface-closure`

## 1. 复评背景

2026-06-14 的初版评估判断 Phase II 尚未达到收束标准，推荐采用“混合方案”：完成 Governance Timeline 前端拆分、Runtime Surface assembler 提取，并定义何时回到 channel 实现的判断标准后，再关闭 Phase II。

截至本次复评，以下关键收口已完成并归档：

- `add-governance-timeline-panel-slimming`
- `extract-runtime-surface-embedded-sdk-assembler`
- `harden-query-run-read-model-contracts`
- `add-embedded-sdk-model-step-contract`
- `add-embedded-sdk-provider-model-step-adapter`
- `add-embedded-sdk-e2e-integration-smoke`
- `add-embedded-sdk-reference-domain-agent`
- `add-domain-agent-sdk-execution`
- `add-domain-agent-execution-smoke`
- `add-embedded-sdk-recovery-acceptance-smoke`

本次复评只判断 Phase II 是否应继续作为默认主线，不新增 runtime 行为、不启用 provider/default chat promotion、不继续做 UI 微优化。

## 2. 收束标准逐项复评

### 标准 1：SDK persistence/recovery 达到下一成熟度

**当前状态：显式消费 readiness 已完成，生产级自动恢复仍不授权。**

已完成：

- SDK persistence interface 已稳定表达 `memory_preview / durable_ready / durable_degraded`。
- workspace store、continuation descriptor、registry-backed reattach、checkpoint/cursor probe、recovery operation evidence 已形成稳定 contract。
- `run_recovery` 已成为 Runtime Surface dedicated read model，暴露 checkpoint、resume cursor、operation history、audit summary。
- `embedded-sdk-recovery-acceptance-smoke-v1` 已能输出 durable registry-backed accepted evidence，并固定 memory-only workspace、missing registry binding 两类 blocked evidence。
- worker ownership、retry、scheduler、child executor dispatch 等 readiness/gate evidence 已进入 contract / smoke / quality gate / snapshot 体系。

仍未授权：

- 默认 production worker lease enforcement。
- 后台自动恢复。
- 分布式 executor。
- 默认 retry scheduler。
- 真实 child executor dispatch。

**评估：达到 Phase II “readiness / controlled consumption”成熟度，但未达到 production automation。生产自动化应进入 Phase III 或后续单独授权 change。**

### 标准 2：Governance 前端拆分为更稳定边界

**当前状态：达到 Phase II 收束线。**

已完成：

- Governance Timeline 已拆出 filter、event card、main chat query workspace、focus summary grid、event stream、overview cards、summary/action cards、framework adapter cards、remediation card、recent snapshot commands card 等子组件。
- `GovernanceTimelinePanel.vue` 已从 1,208 行降到约 884 行。
- 当前主事件流应保持 `GovernanceTimelineEventStream` 为主干，不建议继续拆成更多重叠小卡片。

剩余事项：

- 后续若继续瘦身，应在真实维护痛点出现时做小切片，不再作为 Phase II 默认 blocker。

**评估：通过 Phase II 收束标准。**

### 标准 3：Runtime Surface assembler 方法明确并开始落地

**当前状态：达到 Phase II 收束线。**

已完成：

- `RuntimeSurfaceProfileAssembler` 承接顶层 profile shell。
- `RuntimeSurfaceProfileContextAssembler` 承接 profile request context、runtime scope 与 recovery target 推导。
- `RuntimeCoreContractBuilder` 承接 `runtime_core` shell、scope overlay 与 child merge evidence。
- `ProviderCatalogBuilder` 承接模型过滤、provider 汇总和 `provider_resolution`。
- `EmbeddedSdkRuntimeSurfaceBuilder` 承接 Embedded SDK / Harness 的 factory、bootstrap、default recovery、run recovery 与 recovery alignment read-model 组装。
- Query/Run read model 已硬化：`main_chat_query_detail`、`main_chat_query_history`、`recent_queries` 已具备自描述 metadata，Runtime Surface 与 Governance Timeline 共享解释入口。

剩余事项：

- `GovernanceOverviewContractBuilder` 仍可作为后续低风险 refactor 候选。
- `RuntimeSurfaceService.py` 仍偏大，但主要高价值 contract boundary 已完成，继续按行数优化收益有限。

**评估：通过 Phase II 收束标准。治理 overview shell 抽取不再自动阻塞 Phase II。**

### 标准 4：团队能判断何时回到 channel 实现 vs 留在基础设施主线

**当前状态：达到 Phase II 收束线。**

当前判断规则：

- 若只是增加 provider evidence、query workspace 细节、多 channel history/workspace、UI 细节或更多局部展示，默认暂停。
- 若真实调用方反馈暴露 provider-owned gap、caller loop gap、source/grounding 失败类别，才重新打开 provider/domain-agent 方向。
- 若要扩展 `subagent_lane` 或 `external_adapter` 到 detail/history/workspace，必须先通过 channel promotion gate 或新的 promotion decision。
- 若要推进 SDK recovery production automation，必须另开显式 Phase III / production authorization change，不能把 readiness evidence 当成默认生产授权。

**评估：通过 Phase II 收束标准。**

## 3. 总体复评

| 标准 | 2026-06-14 初评 | 2026-06-17 复评 | 结论 |
|------|------------------|------------------|------|
| SDK persistence/recovery | 60% | readiness / controlled consumption 完成 | 通过 Phase II，生产自动化后置 |
| Governance 前端拆分 | 50% | 约 70%，主边界稳定 | 通过 |
| Runtime Surface assembler | 40% | 主要高价值 builder 已落地 | 通过 |
| 团队判断标准 | 50% | gate / trigger / non-goals 已明确 | 通过 |

**总体结论：Phase II 可以关闭。**

这不是说系统已经达到生产自动化，而是说 Phase II 的目标“恢复实现与交付面瘦身”已经达到足够收束线。继续停留在 Phase II 容易变成局部优化。

## 4. Phase III 推荐入口

Phase III 应从以下方向中选择一个最小切片，不并行发散：

1. **Embedded SDK production recovery authorization slice**
   - 目标：把现有 recovery readiness 与 production authorization 明确连接起来。
   - 候选：PostgreSQL seam + rollout artifact / production enablement input consumer 的受控接线评估。
   - 非目标：默认启用后台自动恢复、worker lease enforcement、retry scheduler。

2. **真实 caller provider loop closure**
   - 目标：基于 `unifiedKnowledgeRAG` 或其他外接项目做显式 provider caller 闭环验证。
   - 前置：必须有真实 caller feedback 或 acceptance gate blocker。
   - 非目标：默认 chat grounding、GraphRAG、source binding automation。

3. **Domain-agent SDK execution hardening**
   - 目标：沿已完成的 domain-agent SDK execution smoke，补真实垂域接入中暴露的最小缺口。
   - 前置：必须来自真实 domain-agent 试接问题。
   - 非目标：agent marketplace、复杂多租户、完整 tool marketplace。

推荐顺序：

1. 先进入 **Embedded SDK production recovery authorization slice**，因为它直接承接 Phase II 最大剩余风险。
2. Provider/domain-agent 方向只在真实调用方触发后恢复。

## 5. 明确暂停项

以下方向不作为默认下一阶段：

- 继续堆 provider/domain-agent evidence。
- 继续扩 `main_chat` query workspace 细节。
- 将 `subagent_lane / external_adapter` 直接推进到 history/workspace。
- 继续拆 Governance Timeline 小卡片。
- 继续按 `RuntimeSurfaceService.py` 行数做无目标 refactor。
- 默认启用 `/api/chat` grounding、GraphRAG、source binding automation 或 final answer policy promotion。

## 6. 关闭决策

**Decision：关闭 Phase II，进入 Phase III 准备。**

下一步 allowed action：

- 新开一个聚焦 change，评估并实现 `Embedded SDK production recovery authorization` 的最小受控切片。

该切片必须继续保持：

- 显式 opt-in。
- fail-closed。
- 不默认启动 worker / retry scheduler / background recovery。
- 不改变默认 chat 或 provider 行为。

---

本评估取代 2026-06-14 初版评估中的“推荐选项 C”。Phase II 已达到关闭条件，后续不再默认用 Phase II 名义继续追加局部优化。
