# surface-sdk-tool-governance-summary

## Why

`sdk_tool_runtime_execution_coverage` is already normalized into Runtime Contract Gate summaries and guarded by snapshot/specs. Governance Timeline compact runtime contract warnings currently show the approved tool continuation bridge, but not the SDK direct ToolRuntime bridge. Operators must expand the payload to distinguish whether SDK direct tool execution is covered.

## What Changes

- Extend runtime contract warning summary text with `sdk_tool=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 SDK ToolRuntime execution behavior，不修改 smoke/quality gate derivation，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
