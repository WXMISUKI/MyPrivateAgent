## Decision

Add `DomainAgentGroundedAnswerPackageService` as a read-only builder over the existing trial surface.

The service accepts either:

- a prebuilt trial report, or
- the same raw evidence payload used by the trial surface

and returns a bounded `grounded_answer_package`.

## Package Shape

```json
{
  "contract_version": "domain-agent-grounded-answer-package-dry-run-v1",
  "agent_id": "ecommerce_support",
  "package_status": "ready",
  "reason_code": "grounded_answer_package_ready",
  "query": "退款政策是什么？",
  "domain": "refund.policy",
  "allowed_citations": ["refund_policy_2026#section-3"],
  "evidence_items": [
    {
      "source_type": "citation",
      "citation": "refund_policy_2026#section-3"
    }
  ],
  "prompt_binding": {
    "prompt_key": "refund_policy",
    "version": "2",
    "status": "active"
  },
  "memory_boundary": {
    "retrieved_knowledge_promotion_mode": "explicit_only",
    "stored_as_memory_by_default": false
  },
  "fallback_policy": "refuse_or_clarify_when_no_evidence",
  "blockers": [],
  "warnings": [],
  "boundary": {
    "provider_invocation": "not_performed",
    "model_invocation": "not_performed",
    "answer_generation": "not_performed",
    "chat_invocation": "not_performed",
    "runtime_behavior_changed": false
  }
}
```

## Rules

- `package_status=ready` only when trial status is `go`.
- `package_status=review` when trial status is `review`.
- `package_status=blocked` when trial status is `blocked`.
- Citation allowlist must be inherited from the grounding decision.
- Fallback policy comes from the grounding decision.
- Prompt binding and memory boundary are copied from trial evidence summaries.
- GraphRAG requests remain blocked.

## Non-Goals

- Do not invoke an LLM.
- Do not compose a final answer.
- Do not call providers.
- Do not write memory, audit, trace, or source bindings.
- Do not alter `/api/chat`, context packing, or prompt injection.
