# surface-embedded-persistence-governance-summary

## Why

`embedded_sdk_persistence_coverage` is already normalized into Runtime Contract Gate summaries and guarded by snapshot/specs. Governance Timeline compact runtime contract warnings currently expose recovery checkpoint/cursor coverage, but not whether the Embedded SDK persistence posture smoke evidence is covered.

## What Changes

- Extend runtime contract warning summary text with `embedded_persistence=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 Embedded SDK persistence behavior，不修改 smoke/quality gate derivation，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
