## 1. Specification

- [x] 1.1 Validate proposal/design/specs for Phase 22 MemoryOps scope and non-goals.
- [x] 1.2 Confirm `agent-memoryops-lifecycle-contract` separates instruction memory, conversation summaries, long-term memory, hot session state, and retrieved evidence.
- [x] 1.3 Confirm `durable-chat-context-compact` delta is representation-only and does not change compact behavior.

## 2. Backend Contract

- [x] 2.1 Add a focused MemoryOps contract service that normalizes existing `AgentMemoryService` runtime contract data.
- [x] 2.2 Map optional `ConversationSummary` records to `conversation_summary` lifecycle entries.
- [x] 2.3 Expose stable posture blocks for hot session state, long-term memory, and retrieved knowledge evidence without implementing new storage.
- [x] 2.4 Add a read-only MemoryOps registry endpoint without changing `/api/chat`, context packing, or prompt injection.

## 3. Documentation

- [x] 3.1 Update the internal control roadmap to mark PromptOps complete and MemoryOps as Phase 22 current work.
- [x] 3.2 Document the MemoryOps lifecycle contract in runtime contracts.
- [x] 3.3 Update the domain agent guide with memory kind boundaries and non-promotion rules.

## 4. Verification

- [x] 4.1 Add focused tests for instruction memory normalization, conversation summary mapping, absent summary behavior, and retrieved evidence posture.
- [x] 4.2 Run focused MemoryOps tests.
- [x] 4.3 Run existing agent memory focused tests.
- [x] 4.4 Run `openspec validate add-agent-memoryops-lifecycle-contract --strict`.
- [x] 4.5 Run `openspec validate --all --strict`.

## 5. Archive

- [x] 5.1 Sync final MemoryOps decisions to canonical specs.
- [x] 5.2 Archive the change after implementation tasks are complete.
