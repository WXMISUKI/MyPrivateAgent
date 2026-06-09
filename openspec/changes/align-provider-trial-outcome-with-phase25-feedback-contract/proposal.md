## Why

MyPrivateAgent 已经具备 unified knowledge provider repo-side trial outcome 导出能力，但当前输出形状更偏向调用方本地 trial 报告，并不能直接作为 `unifiedKnowledgeRAG` Phase 25 feedback 的输入合同。

而 `unifiedKnowledgeRAG` 这一侧已经明确了：

- caller trial outcome input contract
- Phase 25 provider feedback consumption
- Phase 25 follow-up decision matrix

这意味着当前最有价值的下一步不是继续扩 trial 检查，而是把 MyPrivateAgent 的 trial outcome 对齐到 provider 侧能稳定消费的最小 shape。这样两个仓库之间才形成真正的 feedback closure。

## What Changes

- 为 MyPrivateAgent repo-side unified knowledge provider trial outcome 增加一个兼容 Phase 25 的导出形状。
- 让现有 trial outcome 在保留 MyPrivateAgent 本地用途的同时，能够生成 provider-side feedback contract 所需字段。
- 更新相关文档和测试，明确该输出既是 caller-side trial artifact，也是 provider-side feedback input。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `unified-knowledge-capability-runtime`: repo-side trial outcome 增加 provider Phase 25 feedback contract compatibility

## Impact

- Affected code:
  - `backend/capability_runtime/knowledge_provider_trial.py`
  - `scripts/export_unified_knowledge_provider_trial_outcome.py`
- Affected tests:
  - `tests/agent_framework/test_knowledge_provider_trial.py`
- Affected docs:
  - `docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.md`
  - `docs/guides/external_rag_provider_development.md`
- Affected specs:
  - `openspec/specs/unified-knowledge-capability-runtime/spec.md`
