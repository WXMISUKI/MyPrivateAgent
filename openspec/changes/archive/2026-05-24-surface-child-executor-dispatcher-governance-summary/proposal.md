# surface-child-executor-dispatcher-governance-summary

## Why

`child_executor_dispatcher_coverage` is already normalized into Runtime Contract Gate summaries and guarded by smoke/quality gate/snapshot. Governance Timeline compact runtime contract warnings should expose whether the opt-in dispatcher smoke evidence is covered without requiring payload expansion.

## What Changes

- Extend runtime contract warning summary text with `child_executor_dispatcher=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside existing child executor readiness labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 `ChildExecutorDispatcher`、不启用真实 dispatch、不修改 smoke/quality gate derivation。
