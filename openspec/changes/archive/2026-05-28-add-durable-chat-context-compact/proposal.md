## Why

Main chat now has bounded persisted-history packing, but its early-history summary is still generated transiently for each request and cannot be manually refreshed by the user. Long-running agent conversations need a durable compact boundary so operators can intentionally reduce active context while preserving the original message audit trail.

收口对象：主聊天会话的持久化 compact 摘要、手动 compact 入口、后续模型输入对持久摘要的消费。非目标：不删除原始 `messages`，不引入向量检索/长期记忆系统，不改变 Runtime Surface / Governance Timeline payload shape，不接入外部 agent 框架 memory 语义。

## What Changes

- Add a durable conversation summary record for compacted main chat context.
- Add a backend manual compact operation that can be called through an API and by a `/compact` chat command.
- Update main chat context packing to prefer the latest durable summary plus recent messages.
- Preserve original conversation messages for audit/search; compact only changes model input assembly.
- Return compact operation metadata so UI/API callers can see message count, summary preview, and budget settings.
- Add focused backend tests for summary persistence, `/compact` command handling, and packed-input behavior.

## Capabilities

### New Capabilities
- `durable-chat-context-compact`: Defines durable compact summaries and manual compact behavior for main chat conversations.

### Modified Capabilities
- `chat-context-packing`: Main chat context packing now consumes durable compact summaries before transient fallback summaries.

## Impact

- Backend code:
  - `backend/models.py` for a compact summary persistence model.
  - `backend/services/chat_context_packing_service.py` for durable-summary-aware packing.
  - New service boundary for compact generation and persistence.
  - `backend/routers/conversations.py` or `backend/routers/chat.py` for manual compact API.
  - `backend/routers/chat.py` for `/compact` command interception.
- Runtime contracts:
  - Main chat input assembly semantics change by adding a durable summary layer.
  - No Runtime Surface / Governance Timeline payload change in this slice.
- Frontend:
  - No required UI change; users may type `/compact` in chat.
- Documentation:
  - Update architecture docs to describe durable compact vs original message storage.
