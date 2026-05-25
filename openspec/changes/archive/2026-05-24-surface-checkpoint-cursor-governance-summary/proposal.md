# surface-checkpoint-cursor-governance-summary

## Why

`checkpoint_resume_cursor_coverage` is already normalized into Runtime Contract Gate summaries and degraded trace details. Governance Timeline still renders the compact runtime contract warning summary without this field, so operators may need to expand the payload or inspect backend detail text to know whether checkpoint/resume cursor coverage is present.

## What Changes

- Extend runtime contract warning summary text with `checkpoint_cursor=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside the existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 checkpoint/resume cursor backend contract，不新增恢复执行能力，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
