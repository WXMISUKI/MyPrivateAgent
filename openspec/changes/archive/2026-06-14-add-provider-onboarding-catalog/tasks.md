## 1. Catalog Contract

- [x] 1.1 Add a provider onboarding catalog service with entries for knowledge, voice, OCR, layout, and document VLM providers.
- [x] 1.2 Include env var names, default URLs, capability ids, docs, checks, boundaries, and service-provider cross-links in each entry.
- [x] 1.3 Add onboarding references to known live service provider entries.

## 2. API Surface

- [x] 2.1 Add read-only onboarding list endpoint.
- [x] 2.2 Add onboarding detail endpoint with structured not-found errors.
- [x] 2.3 Add onboarding readiness endpoint that returns checks and recommended next action without probing providers.
- [x] 2.4 Register the router in the agent server registry.

## 3. Verification

- [x] 3.1 Add focused service tests for required catalog entries and secret-free payloads.
- [x] 3.2 Add focused route tests for list/detail/readiness and unknown id behavior.
- [x] 3.3 Run focused pytest for onboarding catalog and service-provider cross-link behavior.
- [x] 3.4 Run `openspec validate --all --strict`.

## 4. Documentation and Archive

- [x] 4.1 Update `docs/architecture/runtime_contracts.md` with the onboarding catalog contract.
- [x] 4.2 Update `docs/roadmap/next_phase_hardening.md` with the provider onboarding completion line.
- [x] 4.3 Update `docs/guides/capability_runtime_registry.md` with onboarding API usage.
- [x] 4.4 Sync canonical specs and archive the completed OpenSpec change.
