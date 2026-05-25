# runtime-contract-summary-render-lifecycle-strictness

## Summary

Runtime Contract Gate and degraded trace payloads now fail closed when `approval_lifecycle_recovery_coverage.alignment_smoke` disagrees with its machine-readable evidence fields. The Markdown quality gate summary still renders the column from the boolean flag alone, so a malformed report can visually claim lifecycle recovery coverage even when `replayed / ignored / already_resolved` evidence is inconsistent.

This change applies the same strict evidence check to Markdown summary rendering.

## Scope

- Harden `_render_summary()` approval lifecycle recovery column.
- Add focused tests for inconsistent and complete lifecycle recovery evidence.
- Update runtime contract docs and manual test notes.

## Non-Goals

- No new runtime contract fields.
- No backend API changes.
- No frontend change.
