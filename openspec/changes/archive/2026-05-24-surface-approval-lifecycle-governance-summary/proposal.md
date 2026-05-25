# surface-approval-lifecycle-governance-summary

## Why

`approval_lifecycle_recovery_coverage` is already normalized into Runtime Contract Gate summaries and degraded trace details. Governance Timeline still renders the compact runtime contract warning summary without this field, so operators can see `approval_replay` but not whether the stricter approval lifecycle recovery alignment is covered.

## What Changes

- Extend runtime contract warning summary text with `approval_lifecycle=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside the existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 approval lifecycle backend contract，不修改 recovery gate，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
