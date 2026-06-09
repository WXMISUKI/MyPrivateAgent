## Why

`unifiedKnowledgeRAG` 的 provider 收口已经完成，当前最有价值的下一步不再是继续增强 provider 内部检索策略，而是把 MyPrivateAgent 侧的真实 caller trial 闭环固定下来，验证 caller trial outcome 能稳定回灌到 provider Phase 25 feedback。

这一步的收口对象是“真实 caller -> provider feedback”最小闭环，而不是新的 RAG 算法增强。现在需要把执行入口、推荐 agent/query、输出路径和 reopen gate 写清楚，避免团队重新滑回局部无限优化。

## What Changes

- 为 Phase 26 新增一组 caller-provider live trial closure 文档产物，明确真实 caller 闭环的执行顺序、输入输出合同和成功判定标准。
- 固化最小执行路径：优先使用 `company_profile` 这类已存在的显式 grounded-answer trial / smoke 入口产出真实 caller outcome。
- 说明 MyPrivateAgent 侧下一阶段只做 caller outcome 生成与回传准备，不继续扩 provider 内部 rerank、hybrid retrieval、query rewrite 或 GraphRAG。
- 在 roadmap 中补充本阶段的退出条件与 reopen gate，明确只有真实 caller 反馈才能重新打开 provider 增强工作。

## Capabilities

### New Capabilities

- `caller-provider-live-trial-closure`: 定义 MyPrivateAgent 如何以最小显式 trial 产物支撑 unifiedKnowledgeRAG Phase 25 feedback 闭环

### Modified Capabilities

- `unified-knowledge-capability-runtime`: 增加“真实 caller live trial 闭环优先于 provider 内部增强”的阶段性执行与文档要求

## Impact

- Affected docs:
  - `docs/integration/phase26-caller-provider-live-trial-closure/*`
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/guides/external_rag_provider_development.md`
- Affected specs:
  - `openspec/specs/unified-knowledge-capability-runtime/spec.md`
  - `openspec/changes/document-phase26-caller-provider-live-trial-closure/specs/caller-provider-live-trial-closure/spec.md`
- Non-goals:
  - 不新增 provider runtime 能力
  - 不引入新的检索策略优化 backlog
  - 不启用默认 `/api/chat` grounding
