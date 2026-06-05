## Decision

Add `DomainAgentGroundedAnswerTrialService` as a read-only orchestration layer over existing grounding and promotion services.

The service produces a trial report; it does not compose or stream a final assistant answer.

## API Shape

Add a narrow endpoint:

```text
POST /api/domain-agents/{agent_id}/grounded-answer-trial
```

Request body:

```json
{
  "domain": "refund.policy",
  "query": "退款政策是什么？",
  "evidence_pack": {
    "status": "answerable",
    "allowed_citations": ["refund_policy_2026#section-3"]
  },
  "provider_evidence": {"status": "trial_passed"},
  "promptops_evidence": {"prompt_key": "refund_policy", "version": "2", "status": "active"},
  "memoryops_evidence": {"retrieved_knowledge_promotion_mode": "explicit_only"},
  "eval_evidence": {"overall_status": "passed"},
  "graph_requested": false
}
```

Response body:

```json
{
  "ok": true,
  "trial": {
    "contract_version": "domain-agent-grounded-answer-trial-surface-v1",
    "agent_id": "ecommerce_support",
    "trial_status": "go",
    "recommended_next_action": "start_repo_side_grounded_answer_trial",
    "grounding_decision": {},
    "promotion_decision": {},
    "citation_allowlist": [],
    "blockers": [],
    "warnings": [],
    "boundary": {
      "default_chat_retrieval_injection": "disabled",
      "provider_invocation": "not_performed",
      "answer_generation": "not_performed",
      "source_binding_creation": "not_performed",
      "memory_write": "not_performed",
      "audit_write": "not_performed",
      "graphrag_execution": "not_promoted",
      "runtime_behavior_changed": false
    }
  }
}
```

## Rules

- The endpoint is explicit opt-in and does not share the `/api/chat` path.
- Missing or unknown agents return a blocked trial report, not a generated answer.
- Caller-supplied evidence is treated as input evidence; the service does not call providers.
- Grounding `blocked` and promotion `blocked` result in trial `blocked`.
- Grounding or promotion `review` results in trial `review` unless a blocker exists.
- GraphRAG requests remain blocked until a later GraphRAG promotion.

## Non-Goals

- Do not invoke RAG or GraphRAG providers.
- Do not compose final answers.
- Do not create source bindings.
- Do not store retrieved snippets as memory.
- Do not write audit or trace records.
- Do not alter `/api/chat`, prompt injection, or context packing defaults.
