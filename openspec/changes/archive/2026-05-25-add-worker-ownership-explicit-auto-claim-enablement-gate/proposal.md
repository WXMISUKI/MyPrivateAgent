# Change: Add Worker Ownership Explicit Auto-Claim Enablement Gate

## Summary

Add a read-only, machine-readable enablement gate for worker ownership recovery-entry auto-claim. The gate explains when an explicit auto-claim request would still fail closed because production ownership, entrypoint allowlist, durable ownership, lease validation, rollout decision, idempotency, or audit evidence is incomplete.

## Motivation

The runtime now exposes auto-claim policy and entrypoint allowlist evidence, but `entrypoint_allowlist_ready = true` can still be mistaken for executable auto-claim authorization. A dedicated enablement gate separates "the entrypoint is named" from "auto-claim may run," and gives smoke/quality gates a precise blocked reason.

## Scope

- Add `build_worker_ownership_explicit_auto_claim_enablement_gate_contract(...)`.
- Embed the enablement gate in auto-claim policy evidence.
- Surface enablement status through `worker_ownership.production_gate.sections[name=recovery_entry_auto_claim_policy].evidence`.
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate summaries.
- Keep SDK auto-claim opt-in and disabled by default.

## Non-Goals

- No default recovery entry auto-claim.
- No new API endpoint.
- No claim_run side effect.
- No production rollout or production default ownership enablement.
- No vendor-specific distributed lock implementation.
