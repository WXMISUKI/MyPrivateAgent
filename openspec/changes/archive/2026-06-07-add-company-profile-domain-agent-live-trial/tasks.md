## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and tasks for the company-profile domain agent live trial.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add a minimal `company_profile` domain agent manifest scoped to `company_profile_2025_trial`.
- [x] 2.2 Add focused tests for manifest source scope and live trial retrieve payload.
- [x] 2.3 Update provider integration docs with the explicit company-profile live trial command and boundaries.

## 3. Verification And Archive

- [x] 3.1 Run focused domain-agent live trial tests.
- [x] 3.2 Run `openspec validate add-company-profile-domain-agent-live-trial --strict`.
- [x] 3.3 Export the real company-profile live trial against `http://127.0.0.1:8020`.
- [x] 3.4 Run `openspec validate --all --strict`.
- [x] 3.5 Archive the OpenSpec change after specs are synchronized.
