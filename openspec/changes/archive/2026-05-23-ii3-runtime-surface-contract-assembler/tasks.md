## 1. Refactor Boundary

- [x] 1.1 Extract the bulk of `get_runtime_profile()` assembly into a dedicated assembler or builder module.
- [x] 1.2 Keep `RuntimeSurfaceService.get_runtime_profile()` as a thin orchestration entrypoint with the same external payload shape.

## 2. Regression Coverage

- [x] 2.1 Update focused backend tests to cover the refactored profile assembly path without changing contract expectations.
- [x] 2.2 Confirm contract snapshot guards still pass for the runtime profile after extraction.

## 3. Documentation and Validation

- [x] 3.1 Update runtime contract and roadmap docs to note the assembler boundary change.
- [x] 3.2 Validate the new change with OpenSpec and targeted backend tests.
