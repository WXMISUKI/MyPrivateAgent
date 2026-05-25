## Context

Recovery operation evidence already supports an optional compact `retry` field. Runtime Surface also exposes recovery operation history and an audit summary. However, retry classification is still too implicit: callers can attach retry fields, but there is no single helper that classifies recovery reasons into retryable or terminal status, and the read model does not explicitly surface latest retry terminal reason as a first-class summary signal.

This change sits between evidence-only retry policy and future automatic retry execution. It tightens the contract without starting background scheduling.

## Goals / Non-Goals

**Goals:**

- Add a recovery retry evidence helper that classifies retry status from recovery reason and attempt bounds.
- Preserve retry evidence inside recovery operation records as compact, non-executable data.
- Make recovery audit summary expose retry status counts and latest retry terminal reason.
- Keep Runtime Surface as the read-side truth for retry distribution.
- Update tests and docs so future automatic retry execution can build on the same evidence shape.

**Non-Goals:**

- No automatic retry scheduler.
- No loop that re-invokes `submit_approval` or `resume_run`.
- No new persistence table.
- No new governance trace event type.
- No bypass of worker ownership checks.

## Decisions

1. Put retry classification in `backend/agent_framework/recovery_operations.py`.

   Recovery operation construction already owns compact operation evidence. Keeping retry evidence construction there avoids duplicating retry classification in SDK, Runtime Surface, and governance adapters.

2. Classify terminal reasons explicitly.

   Reasons such as `missing_registered_binding`, `denied`, `already_resolved`, `stale_worker_fencing_token`, and `worker_ownership_lost` should produce terminal retry evidence. Transient reasons can be marked retryable, but this slice still only records evidence.

3. Treat exhaustion as evidence, not execution.

   When `attempt_number >= max_attempts` for a retryable reason, the helper should produce `retry.status = exhausted` and operation evidence can be recorded as failed by the caller. This does not mean the runtime automatically attempted the retry.

4. Extend the audit summary rather than adding a new read model.

   `run_recovery.recovery_audit_summary` already contains retry counts. Adding latest retry status and terminal reason there keeps the read side cohesive and avoids a parallel retry dashboard.

## Risks / Trade-offs

- [Risk] Retry evidence may be mistaken for automatic retry execution.
  - Mitigation: keep `retry_policy.implemented = false` and document that evidence support is separate from execution.
- [Risk] Reason classification may be incomplete.
  - Mitigation: start with known recovery reasons from existing specs and keep unknown reasons non-retryable unless explicitly classified.
- [Risk] Audit summary could grow too broad.
  - Mitigation: only add compact counts and latest terminal reason, not per-attempt execution details.

