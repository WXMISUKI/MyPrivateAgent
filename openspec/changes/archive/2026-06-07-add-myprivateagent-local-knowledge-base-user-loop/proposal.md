## Why

MyPrivateAgent already can call the external unifiedKnowledgeRAG provider and has provider-side trial evidence, but the next useful step is a caller-side local knowledge base user loop that tells a developer or product tester how to actually use the approved local source for business Q&A.

This change closes the local usability loop without expanding provider evidence, enabling default chat retrieval, or moving vector store, OCR, document parsing, or GraphRAG responsibilities into MyPrivateAgent.

## What Changes

- Add a lightweight local knowledge base user-loop package that combines provider corpus trial evidence, explicit domain-agent API smoke evidence, visible source metadata, suggested questions, citation summary, and a go/review/blocked decision.
- Add a small exporter script that writes JSON and Markdown artifacts under `docs/integration/local-knowledge-base-user-loop/`.
- Add focused tests for go, review, blocked, source mismatch, and boundary-preservation outcomes.
- Keep the implementation read-only and explicit; it does not change `/api/chat`, provider data, source bindings, memory, audit, trace, or GraphRAG behavior.

收口对象：MyPrivateAgent 侧“本地知识库真实使用闭环”，也就是调用方如何看见可用 source、用哪个入口提问、如何查看证据和下一步结论。

非目标：

- 不改 unifiedKnowledgeRAG provider 实现。
- 不启用默认 `/api/chat` 检索注入。
- 不创建 source-to-agent binding。
- 不引入向量库、OCR、LlamaIndex、Neo4j 或 GraphRAG 依赖。
- 不做复杂知识库管理后台、权限审计、审批流或生产部署。

## Capabilities

### New Capabilities

- `local-knowledge-base-user-loop`: Covers the caller-side read-only user loop package for an approved local knowledge source, including source visibility, suggested trial questions, evidence summary, and decision output.

### Modified Capabilities

- None.

## Impact

- Affected backend code:
  - New read-only service under `backend/capability_runtime/`.
  - New exporter script under `scripts/`.
- Affected tests:
  - New focused tests under `tests/agent_framework/`.
- Affected docs/artifacts:
  - New generated JSON and Markdown report under `docs/integration/local-knowledge-base-user-loop/`.
  - New canonical OpenSpec capability after archive.
- Runtime/API impact:
  - No runtime default behavior change.
  - No new external dependency.
  - No database migration.
