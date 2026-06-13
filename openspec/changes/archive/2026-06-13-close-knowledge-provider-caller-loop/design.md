## Context

`unifiedKnowledgeRAG` is positioned as a lightweight external knowledge provider. Its provider-side local use loop is now closed: the service can run at `http://127.0.0.1:8020`, expose ready health/preflight/source-binding evidence, and return citation-backed RAG evidence.

MyPrivateAgent owns the caller/control-plane side: provider configuration, capability registry, explicit trial execution, runtime boundaries, and downstream feedback artifacts. Existing Phase 26 docs already describe the caller-provider live trial, but the repository still needs a clean caller-side closure that refreshes evidence and points maintainers at the exact enablement sequence.

## Goals / Non-Goals

**Goals:**
- Keep the caller closure explicit, local, and reproducible.
- Verify `unifiedKnowledgeRAG` through existing MyPrivateAgent scripts and artifacts.
- Document the required MyPrivateAgent environment variables without editing a user's local `.env`.
- Refresh caller-side smoke and provider-compatible trial outcome artifacts.
- Preserve the distinction between provider evidence and MyPrivateAgent runtime behavior.

**Non-Goals:**
- No default `/api/chat` retrieval injection.
- No GraphRAG execution or graph query promotion.
- No source-to-agent binding automation.
- No provider runtime promotion or retrieval backend switch.
- No final answer policy, audit, approval, memory, or governance behavior change.
- No frontend work.

## Decisions

1. Use the existing explicit caller smoke as the primary verification path.
   - Rationale: `backend/scripts/company_profile_explicit_api_local_smoke.py` already exercises the real provider-backed `agent manifest -> provider retrieve -> grounded-answer explicit API` chain.
   - Alternative considered: Add a new smoke command. Rejected because it would duplicate Phase 26 behavior and increase maintenance.

2. Keep provider configuration caller-owned and documented.
   - Rationale: MyPrivateAgent should read `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER` and `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL`; this change should not mutate the user's local `.env`.
   - Alternative considered: Automatically write `.env`. Rejected because secrets/config are local operator state.

3. Treat provider feedback payload as the closure artifact for future provider-side follow-up.
   - Rationale: `unified-knowledge-provider-trial-outcome.json.provider_feedback_input` is the bridge back to `unifiedKnowledgeRAG` Phase 25 feedback, without reopening provider work by default.
   - Alternative considered: Keep only the company-profile API smoke. Rejected because provider-side follow-up needs a normalized feedback input.

4. Keep closure docs separate from default chat behavior.
   - Rationale: Successful explicit retrieval proves caller capability, not a decision to inject retrieval into every chat request.
   - Alternative considered: Update `/api/chat` behavior. Rejected because grounding promotion requires a separate policy/eval-backed change.

## Risks / Trade-offs

- [Risk] Provider service is not running when evidence commands execute. -> Mitigation: The runbook starts with `/health` verification and treats service unavailability as a caller setup issue.
- [Risk] Maintainers misread explicit smoke success as default chat grounding readiness. -> Mitigation: Specs and runbook explicitly state default chat retrieval injection remains disabled.
- [Risk] Caller smoke passes while provider feedback payload is stale. -> Mitigation: Tasks refresh both the explicit smoke and repo-side provider trial outcome.
- [Risk] `.env` is missing provider settings during normal app startup. -> Mitigation: Document required settings and verify registry behavior with focused tests/env-scoped commands rather than changing local secrets.
