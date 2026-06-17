## 1. Specification

- [x] 1.1 Validate the OpenSpec change artifacts before implementation.
- [x] 1.2 Confirm the affected Runtime Surface contracts and non-goals remain limited to Embedded SDK / Harness read-model assembly.

## 2. Implementation

- [x] 2.1 Add a dedicated Embedded SDK Runtime Surface builder module that delegates to existing recovery and embedded runtime bundle builders.
- [x] 2.2 Rewire `RuntimeSurfaceProfileAssembler` to build `embedded_runtime_factory`, `embedded_runtime_bootstrap`, and `default_runtime_recovery` through the new builder.
- [x] 2.3 Rewire `RuntimeSurfaceService` bootstrap and run recovery wrapper methods to use the new builder while preserving current validation ownership.

## 3. Verification

- [x] 3.1 Add or adjust focused backend tests proving embedded runtime profile fields, bootstrap, default recovery, and run recovery payloads remain stable.
- [x] 3.2 Run focused Runtime Surface backend tests for embedded runtime and run recovery contracts.

## 4. Documentation and Archive

- [x] 4.1 Update Runtime Contract and roadmap docs to record the Embedded SDK Runtime Surface builder boundary.
- [x] 4.2 Sync canonical specs, validate all OpenSpec specs strictly, and archive the completed change.
