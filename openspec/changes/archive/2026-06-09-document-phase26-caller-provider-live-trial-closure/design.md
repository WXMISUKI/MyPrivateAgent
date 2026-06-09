## Context

当前两个仓库已经形成明确分工：

- `unifiedKnowledgeRAG`：轻量、通用、read-only 的 RAG provider
- `MyPrivateAgent`：caller、grounded-answer 控制面、trial 执行者

provider 已完成 Phase 25 feedback 消费侧准备，MyPrivateAgent 也已具备 repo-side trial outcome 与显式 grounded-answer trial / smoke 入口。当前缺的不是更多 provider 技巧，而是把“谁来跑 trial、跑哪个入口、产出什么、何时算闭环完成”写成一个可复用执行包。

因此 Phase 26 的设计目标是文档优先收口：

- 选定最小真实 caller 验证入口
- 固化推荐命令、输出路径、成功判定
- 给出 provider reopen gate

## Goals / Non-Goals

**Goals:**

- 让团队明确下一阶段的主线是 caller-provider live trial closure，而不是 provider 内部增强。
- 固化一条最小、稳定、可复现的 caller trial 执行路径。
- 明确 live trial outcome 如何作为 provider Phase 25 feedback 的输入。
- 规定 reopen provider enhancement 的触发条件，避免继续写入局部优化 backlog。

**Non-Goals:**

- 不修改默认 `/api/chat` 检索行为。
- 不新增 rerank、hybrid retrieval、query rewrite、GraphRAG 执行实现。
- 不扩展 source binding automation、audit orchestration、runtime promotion。
- 不把 MyPrivateAgent 变成 provider orchestrator。

## Decisions

### 1. 用文档切片先收口，而不是继续代码增强

- 原因：
  - 当前缺的是团队执行一致性，不是基础能力缺失。
  - 先把执行入口写清楚，可以避免后续每次都重新讨论 phase/边界。
- 备选方案：
  - 直接继续做新的 caller-side exporter 或 provider-side helper。
- 为什么不选：
  - 当前已经有足够多入口，问题在于“下一步该用哪一个、做到哪停”。

### 2. 优先采用已存在的最小真实 caller 入口

- 推荐入口：
  - `company_profile` domain agent live grounded-answer / explicit API smoke
- 原因：
  - 该链路已经存在真实 `agent manifest -> provider retrieve -> grounded-answer trial` 闭环
  - 输入语料和 query 更容易稳定复现
- 备选方案：
  - 直接用更复杂的业务 agent 或多 source trial
- 为什么不选：
  - 会过早引入业务复杂度，掩盖 provider/caller 边界判断

### 3. 把 RAG_Techniques 仅作为 strategy candidates

- 借鉴内容：
  - 真实 trial 驱动优化，而非凭感觉上技术
  - 用 evidence-backed gate 决定是否引入 rewrite/rerank/hybrid
- 不借内容：
  - 不把高星项目里所有 RAG 技巧直接搬进当前 backlog
- 落点：
  - 仅写入 reopen gate 和后续候选策略说明，不进入当前实现任务

### 4. 把 provider reopen 条件固定成少数几类触发器

- 推荐 triggers：
  - `real_caller_feedback_trigger`
  - `provider_owned_gap_trigger`
  - `repeated_cross_source_failure_class_trigger`
  - `runtime_strategy_evaluation_trigger`
- 原因：
  - 避免团队把零散问题都解释成 provider 要继续增强

## Risks / Trade-offs

- [Risk] 文档切片看起来“没有写代码” → Mitigation：明确这是 Phase 26 的执行入口收口，直接为后续真实联调节省反复讨论成本。
- [Risk] 选用 `company_profile` 入口会不会太简单 → Mitigation：先把最小真实闭环跑通，后续再基于真实失败类型升级到更复杂 agent。
- [Risk] 团队可能再次把 `RAG_Techniques` 当默认 backlog → Mitigation：在 runbook 与 roadmap 中明确“只作为候选策略库，不是默认待办”。
