# Add Worker Ownership Vendor Lock Target Decision Input Source

## Why

Worker ownership now exposes a vendor lock target decision gate, but the target decision still lacks a machine-readable source of authority. Before implementing a vendor-specific lock adapter, operators and quality gates need to distinguish an absent decision from a decision that came from explicit config, an operations record, a rollout artifact, or manual approval metadata.

## What Changes

- Add a read-only vendor lock target decision input source contract.
- Embed the input source under `worker_ownership.vendor_lock_semantics.policy.target_decision.input_source`.
- Surface compact input source evidence in the production gate `vendor_lock_semantics` section.
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate coverage to fail closed when input source evidence is absent.

## Non-Goals

- Do not implement a vendor-specific distributed lock adapter.
- Do not infer vendor lock semantics from SQL row lease/fencing.
- Do not enable production worker ownership by default.
- Do not start a background worker or renewal loop.
- Do not enable recovery entry auto-claim by default.
