## Context

The current domain-agent grounded-answer chain is intentionally evidence-first:

1. `DomainAgentGroundedAnswerPromotionService` evaluates readiness evidence.
2. `DomainAgentGroundedAnswerTrialService` returns a trial report.
3. `DomainAgentGroundedAnswerPackageService` builds a deterministic package.
4. `DomainAgentGroundedAnswerCompositionTrialService` creates a bounded preview.

Those services do not call the provider. That was the correct boundary while provider readiness was still being proved. Now that `unifiedKnowledgeRAG` has passed a real MyPrivateAgent-side trial, the next useful slice is a thin live orchestrator that calls provider retrieve explicitly and then reuses the existing chain.

## Goals / Non-Goals

**Goals:**

- Provide one explicit command/service to trial a domain agent against a live document RAG provider.
- Keep source scope constrained to `agent.yaml` declared `rag_sources`.
- Preserve provider/caller boundaries in output.
- Return a compact `go / review / blocked` result with machine-readable blockers.
- Use deterministic downstream package/composition services after retrieve.

**Non-Goals:**

- Do not enable default `/api/chat` retrieval injection.
- Do not generate final LLM answers.
- Do not call GraphRAG execution.
- Do not create source-to-agent binding.
- Do not write memory, audit, trace, or approval records.
- Do not promote Qdrant/BGE/hybrid/pgvector/runtime defaults.
- Do not introduce a UI.

## Decisions

### Decision: Direct provider HTTP retrieve in a thin service

The live trial service will call `/api/rag/retrieve` directly. This avoids requiring MyPrivateAgent chat or the capabilities router to be running, and matches the existing provider-side contract.

### Decision: Existing control chain remains the behavior gate

The service will not duplicate grounding, promotion, package, or composition rules. It will only translate provider retrieve output into:

- `provider_evidence`
- `evidence_pack`
- `documents`

Then it will delegate to existing services.

### Decision: Conservative status mapping

- `go`: provider retrieve succeeded and composition trial is ready.
- `review`: provider retrieve succeeded but evidence is insufficient or downstream trial/package/composition needs review.
- `blocked`: missing agent, missing RAG sources, provider unreachable/invalid, malformed evidence pack, missing required citations, or downstream blocked result.

## Output Shape

The report includes:

- `contract_version`
- `agent_id`, `query`, `domain`, `provider_base_url`
- `live_trial_status`
- `reason_code`
- `provider_retrieve`
- `trial_report`
- `package`
- `composition`
- `blockers`, `warnings`
- `boundary`

## Validation

- Use mocked `httpx` transport for focused unit tests.
- Optionally run the CLI against `http://127.0.0.1:8020` when the provider service is already running.
- Run strict OpenSpec validation before archive.
