## Context

`company_profile_2025_trial` has passed the caller-side local corpus trial against the running unified knowledge provider. The next step should not introduce chat injection, source binding, GraphRAG, or heavier orchestration. It should only prove that a domain agent can explicitly declare that source and run the existing live grounded-answer trial against it.

## Goals

- Add a real `company_profile` domain agent manifest.
- Use the manifest as the only RAG source scope for live provider retrieval.
- Produce one explicit live trial artifact for a company-profile question.
- Preserve the existing control-plane/data-plane boundary.

## Non-Goals

- Do not enable default `/api/chat` retrieval injection.
- Do not create or persist source-to-agent bindings.
- Do not write audit, trace, or memory records.
- Do not mutate provider sources, indexes, OCR pipeline, or GraphRAG state.
- Do not add a new answer composer or domain-specific runtime.

## Decisions

### Dedicated manifest instead of reusing ecommerce support

The company profile corpus is a separate local business source. A dedicated `company_profile` manifest keeps source visibility explicit and prevents sample ecommerce policies from becoming the implicit test surface for company data.

### Reuse the live grounded-answer trial script

The existing script already performs the required flow:

1. read selected domain agent manifest,
2. call provider `/api/rag/retrieve` with manifest `rag_sources`,
3. feed evidence into package dry-run and grounded-answer composition trial,
4. export JSON and Markdown results.

Reusing it avoids new workflow code and keeps this slice focused on integration readiness.

### Artifact path is separate from generic live trial artifacts

The real company profile trial output should live under `docs/integration/company-profile-domain-agent-live-trial/` so it does not overwrite the generic ecommerce live trial example.

## Risks And Mitigations

- Provider not running: report `blocked` and keep the change explicit; the user can restart the provider and rerun the command.
- Provider source missing or not ready: the trial should block or review before any chat workflow depends on it.
- Evidence weak for the chosen query: keep the trial result as review evidence instead of broadening the implementation.
