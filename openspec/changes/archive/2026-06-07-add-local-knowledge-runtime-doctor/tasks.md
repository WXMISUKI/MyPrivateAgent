## 1. Specification

- [x] 1.1 Create proposal, design, delta spec, and tasks for the local knowledge runtime doctor.
- [x] 1.2 Validate the OpenSpec change before implementation.

## 2. Implementation

- [x] 2.1 Add `DoctorRuntimeService.run_knowledge_runtime_report(...)` that delegates to the existing company-profile explicit API smoke service.
- [x] 2.2 Extend `backend/scripts/doctor.py` with `--knowledge-runtime` and provider/API/query options.
- [x] 2.3 Optionally expose the same read-only report through `/api/doctor?knowledge_runtime=true`.
- [x] 2.4 Update the external RAG provider guide with the local doctor command and boundary.

## 3. Verification And Archive

- [x] 3.1 Add focused tests for go, review, blocked, secret redaction, and boundary preservation.
- [x] 3.2 Run focused doctor tests.
- [x] 3.3 Run `openspec validate add-local-knowledge-runtime-doctor --strict`.
- [x] 3.4 Run the local knowledge runtime doctor against `http://127.0.0.1:8020` if the provider is reachable.
- [x] 3.5 Run `openspec validate --all --strict`.
- [x] 3.6 Sync canonical spec and archive the OpenSpec change.
