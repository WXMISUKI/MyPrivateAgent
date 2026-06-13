# Phase 26 Caller-Provider Live Trial Task Pack

## 1. 任务目标

固定下一阶段的最小执行包，避免团队继续在 provider 内部做局部优化。

## 2. 推荐执行顺序

### Step 0：读取 MyPrivateAgent caller-loop 入口

执行前先读取：

```text
docs/integration/knowledge-provider-caller-loop/knowledge-provider-caller-loop.md
```

该入口固定本地 provider 启动、MyPrivateAgent 环境变量、显式 caller smoke、provider feedback payload 和非目标边界。

### Step 1：确认 provider 本地可访问

确认：

- `unifiedKnowledgeRAG` 已启动
- `http://127.0.0.1:8020/health` 可用
- 当前 MyPrivateAgent 进程已设置 `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true`
- 当前 MyPrivateAgent 进程已设置 `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020`

### Step 2：运行最小 caller 显式 smoke

执行：

```powershell
python backend/scripts/company_profile_explicit_api_local_smoke.py `
  --provider-base-url http://127.0.0.1:8020
```

预期产物：

- `docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.json`
- `docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.md`

### Step 3：确认 repo-side provider trial artifact

如果需要刷新 repo-side provider-compatible payload，执行：

```powershell
python scripts/export_unified_knowledge_provider_trial_outcome.py `
  --provider-base-url http://127.0.0.1:8020 `
  --agent-id company_profile
```

预期产物：

- `docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.json`
- `docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.md`

重点检查：

- 顶层 `agent_id`
- `provider_feedback_input`
- `provider_feedback_input.provider_retrieve.allowed_citations`

### Step 4：回灌 provider Phase 25

在 `unifiedKnowledgeRAG` 仓库中使用 MyPrivateAgent 输出的 caller outcome / provider feedback-compatible payload 做后续 feedback 验证。

本任务包只负责把 caller 侧输入准备到位，不在本仓库中重做 provider 分类逻辑。

## 3. Done 定义

满足以下条件即可认为 Phase 26 第一刀完成：

- 最小 caller smoke 可复现
- repo-side provider feedback-compatible payload 可导出
- 团队知道下一步应把哪份产物回灌给 provider
- 文档中已明确 provider reopen gate

## 4. 暂缓项

以下内容暂不进入本 task pack：

- query rewrite
- rerank
- hybrid retrieval
- GraphRAG execution
- 默认 chat grounding
- source binding automation
