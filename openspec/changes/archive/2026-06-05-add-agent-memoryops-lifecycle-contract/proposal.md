## Why

MyPrivateAgent already has layered instruction memory, durable chat compaction, and bounded context packing, but these pieces do not yet share one lifecycle vocabulary. After Grounding Policy and PromptOps are visible, the next control-plane slice needs a lightweight MemoryOps contract so later multi-turn eval and default retrieval promotion can distinguish memory, summary, and retrieved knowledge evidence.

收口对象：MemoryOps 生命周期只读合同、现有 memory/summary 能力的分类映射、注入 trace 可见性。非目标：不实现向量记忆库、不自动写入长期记忆、不改默认 `/api/chat` 行为、不扩展复杂隐私合规平台。

## What Changes

- Add an `agent-memoryops-lifecycle-contract` capability that defines memory kinds, lifecycle statuses, scope, source, confidence, TTL, and injection trace fields.
- Add a lightweight backend read model that maps existing `AgentMemoryService` entries and optional `ConversationSummary` records into MemoryOps registry entries.
- Clarify that retrieved knowledge evidence is not durable memory unless a later explicit promotion flow writes it as memory.
- Expose MemoryOps visibility without changing runtime prompt/context injection behavior.
- Update roadmap and runtime docs to mark PromptOps complete and MemoryOps as Phase 22 current work.
- Non-goals:
  - Do not introduce vector DB, embedding store, semantic long-term memory, or graph memory.
  - Do not auto-promote chat content or RAG results into memory.
  - Do not delete, rewrite, or redact existing conversation messages.
  - Do not implement multi-turn eval or default knowledge injection in this change.

## Capabilities

### New Capabilities

- `agent-memoryops-lifecycle-contract`: Defines the minimal MemoryOps lifecycle registry and compatibility mapping from existing memory and summary services.

### Modified Capabilities

- `durable-chat-context-compact`: Conversation summaries can be represented as `conversation_summary` MemoryOps entries without changing compact behavior.

## Impact

- Affected backend contracts:
  - `backend/services/agent_memory_service.py`
  - `backend/services/chat_context_compact_service.py`
  - New focused MemoryOps contract service.
  - A read-only MemoryOps registry endpoint.
- Affected docs:
  - `docs/roadmap/internal_agent_control_tasks_2026-06-03.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/guides/domain_agent_development_guide.md`
- Affected tests:
  - focused backend tests for lifecycle normalization and registry shape.
- Dependencies:
  - No new runtime dependency.
  - No external provider dependency.
