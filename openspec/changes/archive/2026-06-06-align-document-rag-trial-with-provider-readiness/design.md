## Context

Phase 19 in MyPrivateAgent already proves the minimal provider access path through live HTTP checks. Phase 24 in `unifiedKnowledgeRAG` now closes the provider-side document RAG readiness question and tells callers to begin the repo-side document RAG trial.

Without an explicit link, reviewers must read the provider-side Phase 24 artifact separately from the MyPrivateAgent trial outcome. This change keeps the implementation lightweight by reading the Phase 24 artifact as optional context and recording whether it supports the trial.

## Goals / Non-Goals

**Goals:**

- Keep the repo-side trial as the caller-owned source of truth for MyPrivateAgent trial outcome.
- Record provider-side Phase 24 document RAG readiness closure when available.
- Fail closed on malformed or blocked provider-side readiness evidence when the caller explicitly supplies it.
- Preserve the current HTTP trial checks and output shape.

**Non-Goals:**

- Do not start or manage `unifiedKnowledgeRAG`.
- Do not require a fixed filesystem path to another repository.
- Do not change default `/api/chat` retrieval injection.
- Do not create source-to-agent binding.
- Do not promote retrieval backend defaults or GraphRAG execution.
- Do not store provider API key values in artifacts.

## Decisions

### Decision: Optional explicit readiness path

The trial exporter will accept an optional `--provider-readiness-path`. When omitted, the trial remains compatible with the existing live HTTP-only behavior and records that provider readiness evidence was not supplied.

When supplied, the path is read as JSON. The trial records a `provider_document_rag_readiness` check before the HTTP checks.

### Decision: Readiness check semantics

The readiness check is:

- `ready` when the artifact has `decision=go` and `trial_readiness_state=ready_for_repo_side_document_rag_trial`.
- `blocked` when the artifact is unreadable, malformed, or explicitly blocked.
- `review` for any other valid non-go readiness state.

The HTTP trial remains the final caller-side proof. Provider readiness cannot bypass live checks.

### Decision: Preserve boundary fields

The trial summary will continue to state:

- `source_binding_policy_owner=caller`
- `runtime_promotion_status=unchanged`
- no default chat retrieval injection
- no source-to-agent binding creation

## Risks / Trade-offs

- A supplied stale readiness artifact could mislead reviewers. The artifact timestamp and path are recorded so reviewers can identify staleness.
- Omitting the readiness path keeps older workflows working, but reviewers will not see provider-side Phase 24 context in the outcome.
- A `ready` provider artifact does not prove live reachability; the HTTP trial checks still decide the caller-side outcome.
