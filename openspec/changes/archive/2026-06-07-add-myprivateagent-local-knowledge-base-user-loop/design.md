## Context

The current knowledge provider integration has two useful caller-side artifacts:

- `local_knowledge_provider_corpus_trial` checks provider source visibility, document manifest, retrieve/answer behavior, citation allowlists, and negative-control behavior.
- `business_rag_user_loop_closure` combines corpus trial evidence with an explicit company-profile API smoke and emits a closure decision.

Those artifacts prove integration readiness, but they are still phrased as trial/closure evidence. The next lightweight slice should turn them into a local user-loop package that answers: which local knowledge source is visible, which entry point should a caller use, which questions can be tried first, what citations were observed, and whether local business Q&A can proceed.

## Goals / Non-Goals

**Goals:**

- Produce a MyPrivateAgent-facing local knowledge base user-loop report for `company_profile_2025_trial`.
- Reuse existing corpus trial and explicit API smoke artifacts as read-only inputs.
- Surface source id, provider base URL, endpoint, suggested questions, citations, boundary status, and a go/review/blocked decision.
- Treat weak evidence and negative-control review as caller review/fallback information, not as a provider rewrite trigger.
- Keep the output suitable for local product testing and developer handoff.

**Non-Goals:**

- Do not call the LLM or modify final answer composition.
- Do not enable default chat retrieval injection.
- Do not mutate domain-agent manifests, source bindings, audit, trace, memory, or provider data.
- Do not start external services or OCR/PDF ingestion flows.
- Do not promote GraphRAG.
- Do not add a UI screen in this slice.

## Decisions

1. Build a thin read-only package service instead of expanding provider trial logic.
   - Rationale: provider and caller readiness checks already exist; the missing piece is usability framing for local business Q&A.
   - Alternative considered: add more corpus-quality cases. Rejected for this slice because it continues provider-side local optimization and does not help the user start using the source.

2. Use existing artifacts as inputs instead of making live HTTP calls.
   - Rationale: the package should be reproducible, fast, and runnable without requiring the provider to be up during every MyPrivateAgent test.
   - Alternative considered: call `/api/rag/*` directly. Rejected for default path because that is already covered by `local_knowledge_provider_corpus_trial`.

3. Emit `go`, `review`, or `blocked` based on caller usability, not provider perfection.
   - Rationale: local product testing can continue when answerable cases pass and only negative controls need review; blockers should remain reserved for missing inputs, source mismatch, missing citations, or boundary drift.
   - Alternative considered: require every upstream artifact to be `go`. Rejected because it would turn quality backlog into a usability blocker.

4. Keep the package outside `/api/chat`.
   - Rationale: grounding promotion and default chat retrieval are separate policy decisions. This slice only proves and packages an explicit local knowledge-base usage path.

## Risks / Trade-offs

- Existing input artifacts may be stale -> the report records input paths and generated timestamps so testers know what evidence was consumed.
- A `review` upstream corpus trial can still produce a `go` user-loop when the review is limited to weak negative controls -> the report preserves warnings and recommended actions instead of hiding them.
- No UI is added -> the loop is developer/tester friendly first; a later UI slice can consume the JSON contract if needed.
