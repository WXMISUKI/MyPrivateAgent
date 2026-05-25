# Trace Recovery Retry Evidence Coverage

## Summary
Add recovery retry evidence coverage to degraded Runtime Contract Gate governance traces.

## Problem
`recovery_retry_evidence_coverage` now exists in smoke, Quality Gate, Runtime Contract Gate, and Snapshot, but degraded `runtime_contract_gate_degraded` trace payloads and fingerprints do not yet explicitly normalize this coverage. A retry evidence gate regression could therefore be harder to spot in Governance Timeline, and fingerprint/dedupe behavior could miss coverage-only changes.

## Goals
- Normalize `runtime_contract_summary.recovery_retry_evidence_coverage` before writing degraded Runtime Contract Gate traces.
- Include retry coverage in degraded trace fingerprints and dedupe keys.
- Add a compact trace detail label for retry evidence coverage.
- Keep retry evidence as audit/quality metadata only.

## Non-Goals
- Do not implement automatic retry scheduling or execution.
- Do not change `retry_policy.implemented = false`.
- Do not change Quality Gate smoke behavior from the previous slice.
- Do not change Governance Timeline UI in this slice.
