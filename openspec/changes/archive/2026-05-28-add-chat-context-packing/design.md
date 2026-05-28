## Context

Main chat currently persists every user and assistant message, and it already has an in-process `ContextWindow` plus a separate token-aware compaction helper. The active model request path, however, builds messages from runtime system context and the current user message only. This means persisted history is useful for display/search but not for multi-turn reasoning.

This change adds a small backend boundary for main chat context packing. It keeps the Runtime Core contract posture intact: history packing is an input assembly concern for main chat, not a new external framework integration or a new governance read model.

## Goals / Non-Goals

**Goals:**
- Build model-ready conversation context from persisted `Message` rows for the active `conversation_id`.
- Respect a token budget by preserving system context, a compact summary for older turns, and the most recent turns.
- Ensure the current user message appears exactly once in the final model input.
- Keep the service deterministic and testable without calling a model for summarization.
- Wire the packed context into the existing orchestrator and `AgentHarness` flow with focused tests.

**Non-Goals:**
- No frontend API or display contract change.
- No database schema migration in this slice.
- No LLM-powered summarizer or vector retrieval in this slice.
- No Runtime Surface or Governance Timeline payload change.
- No adoption of external agent framework memory semantics.

## Decisions

1. Introduce `ChatContextPackingService` as a backend service boundary.

   Rationale: context packing needs to combine persisted chat rows, token counting, summary generation, and LangChain message conversion. Keeping this out of `orchestrator.py` prevents the orchestrator from growing another responsibility.

   Alternative considered: extend `ContextWindow`. Rejected for this slice because `ContextWindow` is process-local, not hydrated from the durable conversation store, and currently uses a coarse token estimator.

2. Use deterministic compact summaries for older turns.

   Rationale: this avoids another model call inside every chat request and keeps tests stable. The summary should state how many older turns were compacted and include short excerpts of key user/assistant content. A future change can replace this with a durable LLM summary artifact once the contract is stable.

   Alternative considered: call a compression model using `purpose="compression"`. Rejected for the first slice because it introduces latency, failure modes, and model-provider dependencies before the input boundary is proven.

3. Treat persisted history as the source for prior turns, excluding the just-saved current user row.

   Rationale: `get_or_create_conversation()` saves the current user message before orchestration. Passing raw history plus current input can duplicate the current user message unless the packing boundary explicitly appends the current input once.

4. Apply budget after system layers are built.

   Rationale: runtime knowledge, skills, agent memory, subagent role prompts, and completion instructions are higher-priority system context. Conversation history should fit into the remaining practical budget and degrade to summary + recent turns.

## Risks / Trade-offs

- [Risk] Deterministic summaries can omit important details. -> Mitigation: preserve recent turns verbatim and make the summary conservative, with a future path for durable LLM summaries.
- [Risk] System prompts can consume most of the token budget. -> Mitigation: keep all system messages, then reduce conversation history first; log/metadata can later expose budget pressure if needed.
- [Risk] Duplicate current user message could regress tool planning. -> Mitigation: tests assert the final message list contains the current user input once.
- [Risk] Long assistant/tool outputs can still crowd the budget. -> Mitigation: token-aware recent-turn packing stops before exceeding the budget and falls back to the newest message when necessary.

## Migration Plan

1. Add focused tests for the packing service and orchestrator wiring.
2. Add the service and wire `history_messages` from chat route into orchestrator processing.
3. Run targeted pytest for the new tests and existing chat service tests.
4. Rollback is limited to removing the service wiring; persisted message data remains unchanged.

## Open Questions

- Whether to persist generated summaries as artifacts or dedicated DB records should be handled in a later change after this runtime input boundary is proven.
