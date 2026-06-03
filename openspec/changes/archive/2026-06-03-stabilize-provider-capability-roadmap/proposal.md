## Why

MyPrivateAgent is expanding provider capabilities across ASR, TTS, OCR, Layout, VLM, RAG, GraphRAG, context, prompt management, memory, and evaluation. The project needs a stable OpenSpec-backed task direction so future development does not drift into broad UI work, provider internals inside the main backend, or premature runtime defaults.

收口对象：provider capability 后续路线、外部 RAG / GraphRAG 对接前置条件、Grounding Policy、PromptOps、MemoryOps、多轮评估、多模态与 provider ops 的优先级边界。

非目标：本变更不实现 LlamaIndex、Neo4j GraphRAG、PromptOps、MemoryOps 或多轮评估；不改变默认 `/api/chat` 检索行为；不把向量库、图数据库、Embedding、OCR/VLM 模型依赖引入 MyPrivateAgent 主后端。

## What Changes

- Add a canonical `provider-capability-roadmap` spec.
- Record P0/P1/P2 task direction as stable OpenSpec requirements.
- Clarify that `plan-external-rag-graphrag-provider` remains the active P0 provider line.
- Clarify that MyPrivateAgent should wait for external provider readiness before implementing caller-side integration beyond contract/readiness checks.
- Define each later work item as its own focused OpenSpec change, rather than one large implementation batch.

## Capabilities

### New Capabilities

- `provider-capability-roadmap`: Stable roadmap contract for provider-first capabilities and enterprise Agent platform gaps.

### Modified Capabilities

- None. This change records direction only.

## Impact

- OpenSpec:
  - Adds a canonical roadmap spec after archive.
- Docs:
  - Updates provider capability gap assessment with a stable task ledger and next-stage split.
  - Updates the active external RAG / GraphRAG provider task list with readiness gates.
- Runtime:
  - No runtime behavior change.
- External provider:
  - Confirms external RAG / GraphRAG data-plane work can continue independently until readiness evidence is available.

## Verification

- `cmd /c openspec validate stabilize-provider-capability-roadmap --strict`
- `cmd /c openspec validate --all --strict`
