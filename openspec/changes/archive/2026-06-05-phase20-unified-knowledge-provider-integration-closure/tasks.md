## 1. Specification

- [x] 1.1 Create proposal, design, and delta specs for Phase 20 integration closure.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a read-only Phase 20 closure decision builder.
- [x] 2.2 Add a CLI exporter for the closure decision artifact.
- [x] 2.3 Export the current closure decision under docs.
- [x] 2.4 Update `plan-external-rag-graphrag-provider` task decisions without enabling default chat retrieval injection.
- [x] 2.5 Keep GraphRAG execution and source binding promotion separately gated.

## 3. Verification

- [x] 3.1 Add focused tests for go, review, and blocked closure outcomes.
- [x] 3.2 Run focused backend tests for Phase 19 trial and Phase 20 closure behavior.
- [x] 3.3 Run `openspec validate --all --strict`.

## 4. Archive

- [x] 4.1 Sync canonical specs with the Phase 20 closure decisions.
- [x] 4.2 Mark tasks complete after verification.
- [x] 4.3 Archive `phase20-unified-knowledge-provider-integration-closure`.
