## 1. OpenSpec Guardrail

- [x] 1.1 Create proposal, design, and runtime-surface-contract-assembler spec delta.
- [x] 1.2 Validate the change before implementation.

## 2. Backend Refactor

- [x] 2.1 Move `RuntimeSurfaceProfileAssembler` into `runtime_surface_profile_assembler.py`.
- [x] 2.2 Update `RuntimeSurfaceService` to import the dedicated assembler module while preserving compatibility re-export from `runtime_surface_builders.py`.

## 3. Verification and Docs

- [x] 3.1 Add focused service-level coverage for the dedicated assembler boundary and stable profile shell fields.
- [x] 3.2 Run focused backend tests and OpenSpec validation.
- [x] 3.3 Update runtime contract docs and Phase II roadmap with the new assembler boundary.
