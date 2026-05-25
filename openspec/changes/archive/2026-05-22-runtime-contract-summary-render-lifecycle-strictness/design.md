# Design

The Markdown summary should render `Approval Lifecycle Recovery = yes` only when:

- `alignment_smoke` is truthy;
- `replayed_submission_status == replayed`;
- `ignored_submission_status == ignored`;
- `resolved_recovery_reason == already_resolved`.

This mirrors Runtime Contract Gate and health trace normalization, keeping CI artifact rendering aligned with the backend machine-readable contract.
