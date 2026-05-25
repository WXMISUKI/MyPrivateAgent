# surface-child-executor-dispatch-governance-summary

## Why

`child_executor_dispatch_coverage` is already normalized into Runtime Contract Gate summaries and guarded by snapshot/specs. Governance Timeline compact runtime contract warnings should expose whether dispatch boundary smoke evidence is covered without requiring payload expansion.

## What Changes

- Extend runtime contract warning summary text with `child_executor_dispatch=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside existing child executor readiness labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 `child_executor_dispatch_contract`，不启用真实 dispatch，不修改 smoke/quality gate derivation。
