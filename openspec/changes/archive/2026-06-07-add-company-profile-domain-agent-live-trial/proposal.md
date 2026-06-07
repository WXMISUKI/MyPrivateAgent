## Why

The local provider corpus trial for `company_profile_2025_trial` is already usable through live HTTP. MyPrivateAgent now needs the next smallest caller-side slice: prove that a real domain agent manifest can scope retrieval to that source and feed live document RAG evidence into the existing grounded-answer trial chain.

## What Changes

- Add a minimal `company_profile` domain agent manifest.
- Declare `capabilities.rag_sources: [company_profile_2025_trial]`.
- Keep grounding policy citation-required and scoped to `company.profile`.
- Reuse the existing `backend/scripts/domain_agent_live_grounded_answer_trial.py` live trial.
- Add focused tests that verify the manifest-scoped source and the live trial retrieve payload.
- Export one real trial artifact under `docs/integration/company-profile-domain-agent-live-trial/`.
- Keep this explicit and opt-in: no default `/api/chat` retrieval injection, no source-to-agent binding creation, no audit or memory writes, no provider mutation, no OCR, and no GraphRAG execution.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-agent-live-grounded-answer-trial`: Add a company-profile domain agent live trial scenario using the manifest-declared `company_profile_2025_trial` RAG source.

## Impact

- Affected code:
  - `backend/domain_agents/company_profile/agent.yaml`
- Affected tests:
  - focused domain-agent registry and live trial tests
- Affected docs:
  - external provider guide command example
  - generated live trial artifact
- No default runtime behavior changes.
