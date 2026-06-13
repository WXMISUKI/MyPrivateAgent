# Phase 26 Caller-Provider Live Trial Runbook

## 1. 目的

本 runbook 用于收口下一阶段的真实 caller 闭环验证。

当前目标不是继续增强 `unifiedKnowledgeRAG` provider 内部能力，而是验证以下最小闭环已经成立：

`MyPrivateAgent real caller trial -> caller outcome artifact -> provider_feedback_input -> unifiedKnowledgeRAG Phase 25 feedback`

当前 MyPrivateAgent 侧最小执行入口已收口到：

`docs/integration/knowledge-provider-caller-loop/knowledge-provider-caller-loop.md`

该入口负责说明 provider 启动、MyPrivateAgent 环境变量、显式 caller smoke、provider feedback payload 和边界解释。本文保留 Phase 26 的阶段语义与失败分流规则。

## 2. 当前收口对象

- 真实 caller trial 是否可稳定跑通
- caller outcome 是否能直接作为 provider feedback 输入
- provider 是否能基于该 outcome 做出 `no_provider_action_required / provider_review_required / provider_blocked` 判定

## 3. 非目标

本阶段不做：

- query rewrite
- rerank
- hybrid retrieval
- GraphRAG execution
- 默认 `/api/chat` grounding
- source binding automation
- provider runtime promotion

`D:\AI\AIcode\经验总结与复用目录\知识库与RAG\RAG_Techniques` 当前只作为 strategy candidates，不作为默认待办。

## 4. 推荐最小入口

优先使用已存在的最小真实 caller 入口：

```powershell
python backend/scripts/company_profile_explicit_api_local_smoke.py `
  --provider-base-url http://127.0.0.1:8020
```

如果需要从零执行本地 caller 闭环，先按 `docs/integration/knowledge-provider-caller-loop/knowledge-provider-caller-loop.md` 配置并确认：

- `unifiedKnowledgeRAG` 已启动并通过 health / preflight / source-bindings 检查。
- MyPrivateAgent 当前进程设置了 `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true`。
- MyPrivateAgent 当前进程设置了 `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020`。

原因：

- 已覆盖真实 `agent manifest -> provider retrieve -> grounded-answer explicit API` 链路
- 语料与 query 较稳定
- 仍保持显式、只读、边界清晰

## 5. 推荐输出物

建议先确认以下产物存在且可读：

- `docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.json`
- `docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.md`
- `docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.json`

如果需要直接回灌 provider Phase 25，优先读取：

- `unified-knowledge-provider-trial-outcome.json` 中的 `provider_feedback_input`

## 6. 成功判定

本阶段最小成功标准：

- caller 入口可稳定产出 trial artifact
- artifact 中的 caller/provider evidence 可解释
- `provider_feedback_input` 字段完整可用
- 后续 provider Phase 25 feedback 可直接消费该输入，不需要人工重组 JSON

## 7. 失败分流

如果 trial 失败，不默认解释为 provider 需要增强。

优先分流：

1. caller runtime / explicit API 问题
2. provider contract / availability 问题
3. 语料质量 / citation allowlist 问题
4. 重复出现的 provider-owned failure class

只有第 4 类才建议 reopen provider enhancement。

## 8. Provider Reopen Gate

只有满足以下 trigger 之一，才建议重新打开 provider 能力增强：

- `real_caller_feedback_trigger`
- `provider_owned_gap_trigger`
- `repeated_cross_source_failure_class_trigger`
- `runtime_strategy_evaluation_trigger`

没有上述 trigger 时，不把 `RAG_Techniques` 中的 query rewrite / rerank / hybrid retrieval / GraphRAG 直接放进默认 backlog。
