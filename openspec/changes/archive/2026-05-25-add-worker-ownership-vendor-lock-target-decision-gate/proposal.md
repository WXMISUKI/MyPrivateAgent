# Add Worker Ownership Vendor Lock Target Decision Gate

## Why

Worker ownership now exposes SQL row lease/fencing, renewal supervisor lifecycle, rollout operationalization, and production recovery blockers. The remaining vendor lock gap is still too broad: the runtime can say that vendor lock semantics are missing, but it cannot yet show whether a target backend/adapter decision has been recorded.

## What Changes

- Add a read-only vendor lock target decision contract under worker ownership.
- Embed that contract in `worker_ownership.vendor_lock_semantics.policy.target_decision`.
- Surface target decision blocker evidence in `worker_ownership.production_gate.sections[name=vendor_lock_semantics].evidence`.
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate normalization so missing target decisions are machine-readable.
- Keep SQL row lease/fencing explicitly distinct from vendor-specific distributed lock semantics.

## Non-Goals

- Do not implement a vendor-specific distributed lock adapter.
- Do not enable production worker ownership by default.
- Do not start a background worker or renewal loop by default.
- Do not enable recovery entry auto-claim.
- Do not change SDK recovery execution behavior.
