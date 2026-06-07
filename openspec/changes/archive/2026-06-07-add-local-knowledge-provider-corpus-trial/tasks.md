## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and tasks for local knowledge provider corpus trial.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a local corpus trial service with source catalog, manifest, retrieve, answer, citation allowlist, negative-control, and transport failure checks.
- [x] 2.2 Add a CLI export script with provider URL, source id, case file, top-k, timeout, output directory, and provider API key support.
- [x] 2.3 Add focused tests for go, review, blocked/unreachable, invalid citations, missing source, and secret redaction.
- [x] 2.4 Update guide and architecture docs with the explicit local corpus trial command and boundaries.

## 3. Verification And Archive

- [x] 3.1 Run focused local corpus trial tests.
- [x] 3.2 Run `openspec validate add-local-knowledge-provider-corpus-trial --strict`.
- [x] 3.3 Export the real `company_profile_2025_trial` trial against `http://127.0.0.1:8020`.
- [x] 3.4 Run `openspec validate --all --strict`.
- [x] 3.5 Archive the OpenSpec change after specs are synchronized.
