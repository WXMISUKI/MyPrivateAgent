# Implement worker ownership renewal supervisor opt-in seam

## Summary

Add an explicit, side-effect-bounded worker ownership renewal supervisor seam that can renew a lease once when called directly, while keeping background renewal disabled by default.

## Motivation

Worker ownership production gating already explains that heartbeat operations exist but production-grade renewal supervision is missing. The next safe step is to make the renewal boundary executable under explicit test control without starting worker threads, timers, or default recovery auto-claim.

## Non-Goals

- Do not start a background supervisor.
- Do not enable production worker ownership by default.
- Do not implement vendor-specific distributed locks.
- Do not enable recovery entry auto-claim.
- Do not change child executor dispatch.
