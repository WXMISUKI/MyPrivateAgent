## Context

`ChatContextPackingService` now builds bounded model input from persisted conversation messages, but compacted older history is transient. Mature agent workflows usually allow manual compaction and continue from a durable summary while retaining the original transcript for audit/search. This project should add that boundary without expanding the governance surface or replacing the existing SQL conversation store.

## Goals / Non-Goals

**Goals:**
- Persist latest compact summaries per conversation.
- Allow manual compact through an authenticated backend API and `/compact` chat command.
- Let model input use the latest durable compact summary plus recent messages.
- Keep original `messages` rows unchanged for audit and search.
- Keep implementation deterministic and locally verifiable.

**Non-Goals:**
- No vector memory or semantic retrieval.
- No deletion or rewriting of original chat messages.
- No frontend UI redesign.
- No Runtime Surface / Governance Timeline payload expansion.
- No external framework memory adapter.

## Decisions

1. Add a `ConversationSummary` ORM model.

   The record stores `conversation_id`, `summary`, `message_count`, `last_message_id`, `trigger`, optional `instructions`, and timestamps. This gives the packing layer a durable read boundary without changing the original message contract.

   Alternative considered: store summaries only as generic artifacts. Rejected because context packing needs fast, direct lookup by conversation and latest message id; artifacts remain broader runtime outputs.

2. Use deterministic summary generation in this slice.

   The compact service will build a stable summary from user/assistant excerpts and counts. A future change can add model-backed compression using `purpose="compression"` after the persistence and command boundary are stable.

3. Treat `/compact` as a command, not a model prompt.

   Chat routes should intercept messages that start with `/compact`, run the compact service, save a short assistant confirmation, and return without invoking the orchestrator. This mirrors mature agent UX while keeping command handling local.

4. Use existing SQLAlchemy table creation pattern for local compatibility.

   The project currently uses SQLite by default and many smoke paths initialize tables through metadata. This slice adds the model and relies on app startup/create_all paths instead of introducing a risky migration-focused change.

## Risks / Trade-offs

- [Risk] Deterministic summary quality is lower than LLM compact. -> Mitigation: keep original messages, include user-provided instructions in the summary metadata, and leave a future model-backed compact extension.
- [Risk] Summary becomes stale as new messages arrive. -> Mitigation: packing uses latest durable summary only for messages up to `last_message_id`; recent messages after that id still enter verbatim.
- [Risk] Slash command may surprise users who intend literal text. -> Mitigation: only intercept exact `/compact` prefix at the start of a chat message.
- [Risk] Existing DB may lack the new table. -> Mitigation: ensure table creation can be invoked through existing metadata initialization paths and compact service can create the table defensively when first used.

## Migration Plan

1. Add ORM model and compact service.
2. Add API and `/compact` command handling.
3. Update packing service to consume latest summary plus post-summary recent messages.
4. Run targeted backend tests.
5. Archive the change after tasks complete.

## Open Questions

- Model-backed compression and configurable budgets should be a follow-up after deterministic durable compact is stable.
