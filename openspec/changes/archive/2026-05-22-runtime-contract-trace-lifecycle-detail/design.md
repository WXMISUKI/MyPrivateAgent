# Design

The trace detail remains a compact one-line diagnostic string.

Current:

```text
failed_check_count=1
```

New:

```text
failed_check_count=1 approval_lifecycle=covered
```

Mapping:

- `covered` when normalized `approval_lifecycle_recovery_coverage.alignment_smoke` is true.
- `missing` when the coverage object exists but `alignment_smoke` is false.
- `unknown` when no summary object is present.

The trace payload remains the source of truth. The detail string is only a quick backend governance hint.
