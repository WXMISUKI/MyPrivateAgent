# Design

Approval lifecycle recovery coverage is healthy only when all of these are true:

- `alignment_smoke` is truthy;
- `replayed_submission_status == replayed`;
- `ignored_submission_status == ignored`;
- `resolved_recovery_reason == already_resolved`.

Runtime Contract Gate and health trace normalization both recompute `alignment_smoke` using the same predicate. This preserves diagnostics while preventing stale or hand-written artifacts from claiming lifecycle alignment without the required machine-readable evidence.
