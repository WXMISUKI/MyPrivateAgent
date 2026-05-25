# Design

Add a derived summary object:

```json
{
  "approval_lifecycle_recovery_coverage": {
    "alignment_smoke": true,
    "replayed_submission_status": "replayed",
    "ignored_submission_status": "ignored",
    "resolved_recovery_reason": "already_resolved"
  }
}
```

The source of truth is the `approval_lifecycle_recovery_alignment` contract check emitted by `runtime_contract_smoke.py`.

The field is considered covered only when:

- the check itself is `ok`;
- `replayed_submission_status == replayed`;
- `ignored_submission_status == ignored`;
- `resolved_recovery_reason == already_resolved`.

Older reports without this check normalize to `alignment_smoke = false` with empty status/reason strings.
