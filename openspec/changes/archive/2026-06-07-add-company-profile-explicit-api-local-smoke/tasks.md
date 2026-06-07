## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and tasks for the explicit API local smoke.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a local smoke service/exporter that calls the explicit domain-agent API through TestClient.
- [x] 2.2 Add a CLI script with provider URL, API key, agent id, domain, query, top-k, timeout, and output directory options.
- [x] 2.3 Export compact JSON and Markdown smoke artifacts with go/review/blocked decision and redacted secrets.
- [x] 2.4 Update integration docs with the local smoke command and boundaries.

## 3. Verification And Archive

- [x] 3.1 Add focused tests for go, blocked provider, API key redaction, Chinese query preservation, and boundary checks.
- [x] 3.2 Run focused smoke tests.
- [x] 3.3 Run `openspec validate add-company-profile-explicit-api-local-smoke --strict`.
- [x] 3.4 Run the real local smoke against `http://127.0.0.1:8020` if the provider is reachable.
- [x] 3.5 Run `openspec validate --all --strict`.
- [x] 3.6 Archive the OpenSpec change after specs are synchronized.
