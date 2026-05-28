## 1. Tests First

- [x] 1.1 Add focused failing tests for chat context packing summary, recent history preservation, token budget behavior, and current-message dedupe.
- [x] 1.2 Add focused failing test for orchestrator message building with packed persisted history.

## 2. Core Implementation

- [x] 2.1 Implement the chat context packing service boundary with deterministic summary and token-aware recent-message selection.
- [x] 2.2 Wire persisted `history_messages` from chat routes into orchestrator processing.
- [x] 2.3 Update orchestrator message construction to include packed history after runtime system layers and before the current user message.

## 3. Verification And Docs

- [x] 3.1 Run targeted backend tests for the new context packing behavior.
- [x] 3.2 Sync the relevant architecture/runtime documentation with the new main chat context packing boundary.
