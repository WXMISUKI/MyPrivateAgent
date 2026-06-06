## Decision

Add `DomainAgentGroundedAnswerCompositionTrialService` as the last controlled layer above package dry-run.

The service does not invoke a provider. It returns a deterministic preview string and associated machine-readable composition metadata so callers can validate the final shape before any future answer-generation promotion.

## Composition Shape

```json
{
  "contract_version": "domain-agent-grounded-answer-composition-trial-v1",
  "agent_id": "ecommerce_support",
  "composition_status": "ready",
  "reason_code": "grounded_answer_composition_ready",
  "answer_preview": "根据 refund_policy_2026#section-3，退款政策如下。",
  "used_citations": ["refund_policy_2026#section-3"],
  "composition_policy": {
    "mode": "deterministic_preview",
    "citation_mode": "allowlist_only",
    "fallback_policy": "refuse_or_clarify_when_no_evidence"
  },
  "fallback_behavior": {
    "when_blocked": "refuse_or_clarify_when_no_evidence"
  },
  "blockers": [],
  "warnings": [],
  "boundary": {
    "provider_invocation": "not_performed",
    "model_invocation": "not_performed",
    "chat_invocation": "not_performed",
    "runtime_behavior_changed": false
  }
}
```

## Rules

- `composition_status=ready` only when package status is `ready`.
- `composition_status=review` when package status is `review`.
- `composition_status=blocked` when package status is `blocked`.
- Used citations must be a subset of package allowlist.
- Graph blockers remain blockers.
- The preview remains deterministic and policy-shaped; it is not a live LLM answer.

## Non-Goals

- Do not change default `/api/chat`.
- Do not invoke models or providers.
- Do not write memory, audit, trace, or source bindings.
- Do not promote GraphRAG.
