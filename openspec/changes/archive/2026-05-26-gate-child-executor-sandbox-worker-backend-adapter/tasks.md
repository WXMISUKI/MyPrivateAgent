## 1. Runtime Contract Coverage

- [x] 1.1 Add a dedicated sandbox worker backend adapter smoke check covering ready contract, missing guard fail-closed, unsafe payload fail-closed, compact attempt envelope, and invocation count.
- [x] 1.2 Normalize the smoke result into `runtime_contract_summary.child_executor_sandbox_backend_coverage` in Quality Gate.
- [x] 1.3 Normalize and fail-close the same coverage in Runtime Contract Gate.
- [x] 1.4 Add Runtime Contract Snapshot stable field guards for the sandbox backend coverage object and smoke flag.

## 2. Tests And Documentation

- [x] 2.1 Add or update focused unit tests for smoke, Quality Gate, Runtime Contract Gate, and Snapshot degradation.
- [x] 2.2 Update runtime contract architecture docs, roadmap, and canonical spec to describe the new coverage.
- [x] 2.3 Run focused backend tests and contract validation commands.
- [x] 2.4 Mark tasks complete and archive the OpenSpec change after verification.
