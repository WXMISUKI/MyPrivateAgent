## Decision

Create a minimal `DomainAgentGroundedAnswerPromotionService` that combines existing evidence into a single promotion decision.

The service is intentionally a read model:

- It reads domain-agent registry data.
- It calls or consumes the existing grounding policy decision.
- It consumes already-built evidence dictionaries for provider readiness, PromptOps, MemoryOps, and multi-turn eval.
- It does not call an external provider.
- It does not generate an answer.
- It does not write source bindings, audit rows, memory records, or chat context.

## Contract Shape

The output uses a compact stable dictionary:

```json
{
  "contract_version": "domain-agent-grounded-answer-promotion-gate-v1",
  "agent_id": "ecommerce_support",
  "decision": "go",
  "reason_code": "grounded_answer_trial_ready",
  "recommended_next_action": "start_repo_side_grounded_answer_trial",
  "blockers": [],
  "warnings": [],
  "evidence_summary": {
    "provider": {"status": "ready"},
    "grounding": {"decision": "allowed"},
    "promptops": {"status": "active"},
    "memoryops": {"retrieved_knowledge_promotion_mode": "explicit_only"},
    "eval": {"overall_status": "passed"}
  },
  "boundary": {
    "default_chat_retrieval_injection": "disabled",
    "provider_invocation": "not_performed",
    "answer_generation": "not_performed",
    "source_binding_creation": "not_performed",
    "memory_write": "not_performed",
    "graphrag_execution": "not_promoted",
    "runtime_behavior_changed": false
  }
}
```

## Decision Rules

- `blocked` when the agent id is missing or unknown.
- `blocked` when GraphRAG is requested before a separate GraphRAG promotion gate.
- `blocked` when provider evidence is missing, degraded, or explicitly not ready.
- `blocked` when grounding decision is `blocked`.
- `review` when grounding decision is `review`.
- `review` when PromptOps evidence is missing or not active/review.
- `review` when MemoryOps evidence does not prove retrieved knowledge remains explicit-only.
- `blocked` when multi-turn eval evidence is `blocked` or `failed`.
- `go` only when all required evidence is ready enough for a repo-side grounded answer trial.

## Non-Goals

- Do not enable default `/api/chat` retrieval injection.
- Do not call RAG, GraphRAG, PromptOps, MemoryOps, or eval providers automatically.
- Do not compose final answers.
- Do not create source-to-agent bindings.
- Do not write audit events or long-term memory.
- Do not promote GraphRAG execution.
