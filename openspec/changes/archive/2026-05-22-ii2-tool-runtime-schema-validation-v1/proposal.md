## Why

`ToolRuntimeService.execute_tool(...)` currently validates only required
arguments. That catches missing input but still allows obvious schema drift such
as `case_id = 123`, unsupported enum values, or incomplete object payloads.

This change adds a lightweight schema validation v1 to the synchronous tool
runtime adapter. It is intentionally smaller than a full JSON Schema engine so
the runtime contract remains predictable and dependency-light.

## What Changes

- Extend tool arg validation beyond required fields.
- Support a small schema subset:
  - primitive `type`
  - `enum`
  - nested object `required`
- Return compact machine-readable validation errors in
  `execution.schema_validation`.
- Update runtime contract/docs to describe the supported subset.

## Non-Goals

- Do not add a full JSON Schema dependency.
- Do not support coercion, `oneOf`, `anyOf`, arrays, regex patterns, numeric
  ranges, or recursive schemas in this change.
- Do not execute tools when schema validation fails.
