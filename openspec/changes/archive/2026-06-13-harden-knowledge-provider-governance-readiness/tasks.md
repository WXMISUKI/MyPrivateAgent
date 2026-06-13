## 1. Knowledge Provider Readiness Contract

- [x] 1.1 Add a compact `governance_readiness` builder for the external knowledge HTTP provider health payload.
- [x] 1.2 Ensure readiness distinguishes explicit RAG readiness, source catalog posture, GraphRAG gate, and default chat grounding gate.

## 2. Focused Tests

- [x] 2.1 Add provider tests for ready, degraded catalog, and unreachable readiness payloads.
- [x] 2.2 Confirm existing capability registry behavior remains unchanged when the provider is unconfigured.

## 3. Docs and Specs

- [x] 3.1 Sync the canonical `unified-knowledge-capability-runtime` spec with the readiness requirements.
- [x] 3.2 Update runtime contracts, roadmap, and capability runtime guide with the new readiness boundary.

## 4. Verification and Archive

- [x] 4.1 Run focused capability tests and `openspec validate --all --strict`.
- [x] 4.2 Archive the completed OpenSpec change after specs are synced.
