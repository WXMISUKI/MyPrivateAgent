## 1. Promotion Gate Evidence Wiring

- [x] 1.1 Add provider evidence normalization for `governance_readiness`.
- [x] 1.2 Preserve legacy provider evidence fallback for existing trial payloads.

## 2. Focused Tests

- [x] 2.1 Add tests for RAG-ready governance readiness producing `go`.
- [x] 2.2 Add tests for unreachable provider readiness blocking promotion.
- [x] 2.3 Add tests for graph requested with `graph_query.status=gated` blocking promotion.
- [x] 2.4 Add tests for degraded source catalog producing review or blocked without provider calls.

## 3. Docs and Specs

- [x] 3.1 Sync canonical promotion gate spec with the new readiness consumption requirements.
- [x] 3.2 Update runtime contracts and roadmap with the new promotion gate evidence boundary.

## 4. Verification and Archive

- [x] 4.1 Run focused promotion gate tests and `openspec validate --all --strict`.
- [x] 4.2 Archive the completed OpenSpec change after specs are synced.
