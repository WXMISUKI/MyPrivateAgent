# surface-approved-tool-governance-summary

## Why

`approved_tool_execution_coverage` is already normalized into Runtime Contract Gate summaries and degraded trace payloads. Governance Timeline still renders the compact runtime contract warning summary without this field, so operators may need to expand the payload to know whether approved tool continuation execution is covered by smoke/gate evidence.

## What Changes

- Extend runtime contract warning summary text with `approved_tool=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside the existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 approved tool execution backend contract，不修改 approval lifecycle/recovery gate，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
