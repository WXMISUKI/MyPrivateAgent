## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and task list for provider-readiness-aligned document RAG trial outcome.

## 2. Implementation

- [x] 2.1 Add optional provider readiness closure parsing to the repo-side knowledge provider trial service.
- [x] 2.2 Add CLI support for `--provider-readiness-path` without storing secrets or hardcoding another repo path.
- [x] 2.3 Update generated trial outcome artifacts with provider readiness linkage.

## 3. Verification

- [x] 3.1 Add focused tests for ready, blocked, and omitted provider readiness artifact behavior.
- [x] 3.2 Run focused knowledge provider trial tests.
- [x] 3.3 Run `openspec validate align-document-rag-trial-with-provider-readiness --strict`.

## 4. Archive

- [x] 4.1 Mark tasks complete after verification.
- [x] 4.2 Archive the change and run `openspec validate --all --strict`.
