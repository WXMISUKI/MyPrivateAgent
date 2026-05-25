# Change: Enforce Worker Ownership Auto-Claim Enablement Gate in SDK

## Summary

Add an explicit SDK opt-in mode that evaluates the worker ownership auto-claim enablement gate before calling `claim_run`. The existing default and legacy opt-in auto-claim seam remain unchanged.

## Motivation

The runtime now exposes a read-only explicit auto-claim enablement gate, but SDK opt-in auto-claim can still call `claim_run` directly when no descriptor ownership evidence exists. This slice connects the gate to the SDK execution seam in a controlled, opt-in way without changing production defaults.

## Scope

- Add an explicit SDK constructor flag for gate-enforced auto-claim.
- Evaluate the enablement gate before `claim_run` when the new flag is enabled.
- Return fail-closed worker ownership evidence when the gate is blocked.
- Keep legacy `worker_ownership_auto_claim_enabled=True` behavior compatible unless the new gate-enforced flag is set.
- Add focused SDK tests for default, legacy opt-in, blocked gate, non-allowlisted entrypoint, and ready gate paths.

## Non-Goals

- No default recovery auto-claim.
- No production ownership enablement.
- No vendor-specific distributed lock implementation.
- No background worker or supervisor start.
- No API endpoint changes.
