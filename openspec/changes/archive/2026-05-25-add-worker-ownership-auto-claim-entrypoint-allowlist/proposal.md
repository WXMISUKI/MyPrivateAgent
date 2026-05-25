# Change: Add Worker Ownership Auto-Claim Entrypoint Allowlist

## Summary

Add a read-only, machine-readable allowlist contract for worker ownership recovery-entry auto-claim. The contract explains which runtime entrypoints may ever be considered for explicit auto-claim while keeping auto-claim disabled by default.

## Motivation

Worker ownership now has durable lease evidence, opt-in renewal lifecycle, audit evidence, and rollout operationalization blockers. The remaining auto-claim policy still exposes `entrypoint_allowlist` as a coarse missing section. This makes it hard for smoke and quality gates to distinguish "the allowlist itself is defined" from "auto-claim remains blocked because production enablement, idempotency, audit, and rollout are not complete."

## Scope

- Add `build_worker_ownership_auto_claim_entrypoint_allowlist_contract(...)`.
- Embed allowlist status and allowed entrypoints in auto-claim policy evidence.
- Surface allowlist evidence through `worker_ownership.production_gate.sections[name=recovery_entry_auto_claim_policy].evidence`.
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate summaries.
- Keep SDK auto-claim opt-in and disabled by default.

## Non-Goals

- No default recovery entry auto-claim.
- No new API endpoint.
- No production rollout enablement.
- No vendor-specific distributed lock implementation.
- No child executor dispatch work.
