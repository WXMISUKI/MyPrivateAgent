## Context

The project has several memory-adjacent pieces:

- `AgentMemoryService` loads instruction-like memory layers from files and already emits `MemoryEntry` objects.
- `ChatContextCompactService` persists conversation summaries for `/compact`.
- `ChatContextPackingService` consumes durable summaries and recent messages when assembling model input.
- External knowledge retrieval returns evidence, but it should not be treated as durable memory by default.

These are useful, but callers lack one machine-readable registry that explains kind, lifecycle, source, scope, confidence, TTL, status, and injection posture. Phase 22 should add that vocabulary without changing chat behavior.

## Goals / Non-Goals

**Goals:**

- Define memory kinds:
  - `runtime_instruction_memory`
  - `conversation_summary`
  - `hot_session_state`
  - `long_term_memory`
  - `retrieved_knowledge_evidence`
- Define lifecycle statuses:
  - `candidate`
  - `active`
  - `expired`
  - `deleted`
  - `conflicted`
  - `disabled`
- Normalize existing `AgentMemoryService` entries into `runtime_instruction_memory` records.
- Normalize optional `ConversationSummary` objects into `conversation_summary` records.
- Expose injection trace metadata as visibility-only, including whether an entry is currently injected by existing runtime paths.
- Preserve fail-open behavior when memory services or summaries are absent.

**Non-Goals:**

- No semantic vector memory.
- No automatic long-term memory write path.
- No memory conflict resolver.
- No privacy deletion workflow beyond status vocabulary.
- No change to `/api/chat`, context packing, or prompt injection behavior.
- No UI work.

## Decisions

1. **MemoryOps starts as a registry read model.**
   - Decision: Build a `MemoryOpsContractService` that accepts existing memory contracts and summary records, then returns a bounded registry.
   - Alternative considered: Create a new `memories` table immediately.
   - Rationale: Existing services already own real data. A read model gives lifecycle vocabulary without migration risk.

2. **Instruction memory and conversation summary are first-class kinds.**
   - Decision: Map `AgentMemoryService.memory_entries` to `runtime_instruction_memory` and `ConversationSummary` to `conversation_summary`.
   - Alternative considered: Treat both as generic memory.
   - Rationale: Runtime instruction layers and conversation summaries have different ownership, TTL, and injection semantics.

3. **Retrieved knowledge evidence is explicitly not memory by default.**
   - Decision: The registry can list capability posture for `retrieved_knowledge_evidence`, but retrieved snippets remain evidence unless promoted later.
   - Alternative considered: Store every retrieval as memory.
   - Rationale: Automatic promotion would create privacy, correctness, and stale-data risks.

4. **Injection trace is descriptive.**
   - Decision: Entries expose `injection_trace.mode = visibility_only` or `existing_runtime_path`, but this change does not alter injection.
   - Alternative considered: Route context assembly through MemoryOps immediately.
   - Rationale: Behavior changes need multi-turn eval after the contract is stable.

## Risks / Trade-offs

- [Risk] The registry may look more capable than the implementation. -> Mitigation: include explicit posture fields for unavailable long-term memory and retrieved-knowledge promotion.
- [Risk] Existing `MemoryEntry` lacks lifecycle fields. -> Mitigation: apply deterministic defaults such as `status=active`, `ttl_policy=none`, and `confidence=1.0`.
- [Risk] Conversation summaries are per-conversation and not globally listable without a DB query. -> Mitigation: the first endpoint accepts optional `conversation_id` and remains useful even without one.

## Migration Plan

1. Add OpenSpec requirements.
2. Implement `MemoryOpsContractService`.
3. Add a read-only endpoint returning the MemoryOps registry.
4. Add focused tests for instruction memory, conversation summary, absent summary, and retrieved knowledge non-promotion posture.
5. Update docs and roadmap.
6. Sync canonical specs and archive.

Rollback: remove the read-only service/endpoint and docs. Existing memory, compact, and chat paths remain unchanged.

## Open Questions

- Should a later durable long-term memory table be owned by the learning subsystem or a separate MemoryOps schema?
- Should memory activation require a multi-turn eval gate once MemoryOps starts affecting context assembly?
