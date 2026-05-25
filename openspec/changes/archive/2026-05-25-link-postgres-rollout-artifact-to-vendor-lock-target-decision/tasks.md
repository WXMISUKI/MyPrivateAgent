## 1. Specification

- [x] Add runtime worker ownership requirements for PostgreSQL target artifact binding evidence.
- [x] Add production gate requirements for smoke/quality coverage of the binding.

## 2. Implementation

- [x] Add `build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(...)`.
- [x] Bridge complete artifact evidence into vendor lock target decision input and target decision contracts.
- [x] Export the new builder.
- [x] Extend runtime smoke evidence for default and complete-artifact binding paths.
- [x] Extend Quality Gate and Runtime Contract Gate summaries.

## 3. Documentation

- [x] Update runtime contract docs.
- [x] Update next phase hardening notes.

## 4. Verification

- [x] Run focused backend unittest suite.
- [x] Run runtime contract smoke.
- [x] Run quality gate report.
- [x] Validate the OpenSpec change and canonical specs.
- [x] Archive the OpenSpec change.
