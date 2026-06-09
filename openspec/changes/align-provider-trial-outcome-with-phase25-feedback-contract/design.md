## Context

当前两个仓库已经分别准备好了：

- MyPrivateAgent: caller-side repo trial execution and outcome export
- unifiedKnowledgeRAG: provider-side Phase 25 feedback consumption

缺口在于两边的 artifact shape 还没有完全对齐。

如果不补这层兼容，团队仍然需要手工转换字段或重新整理 JSON，导致真实 trial 到 provider follow-up 之间不能无缝闭环。

## Goals / Non-Goals

**Goals**

- 让 MyPrivateAgent 的 repo-side trial outcome 能直接满足 provider Phase 25 所需的核心字段。
- 保留现有 MyPrivateAgent trial outcome 的 caller-side价值。
- 保持 read-only、轻量、boundary-safe。

**Non-Goals**

- 不改 provider Phase 25 的语义。
- 不把 MyPrivateAgent 变成 provider orchestrator。
- 不新增默认 chat grounding。
- 不新增 source binding、approval、audit 流程。

## Decisions

- 采用“兼容扩展”而不是“替换原结构”：
  - 保留当前 trial outcome 主结构
  - 增加 provider-side feedback contract 所需字段或兼容 payload

- 关键目标字段应覆盖：
  - `live_trial_status`
  - `reason_code`
  - `provider_base_url`
  - `agent_id`
  - `query`
  - `provider_retrieve.status`
  - `provider_retrieve.reason_code`
  - `provider_retrieve.document_count`
  - `provider_retrieve.evidence_pack_status`
  - `provider_retrieve.citation_policy`
  - `provider_retrieve.allowed_citations`

- 如果当前 repo-side trial 还没有足够信息，就用保守默认或 review-level mapping，而不是伪造 ready 语义。

## Risks / Trade-offs

- 如果兼容层写太重，会污染本地 trial artifact -> 保持只添加 Phase 25 需要的最小字段。
- 如果 mapping 太乐观，会误导 provider-side follow-up -> 保持 fail-closed，信息不足时导出 review-compatible shape。
