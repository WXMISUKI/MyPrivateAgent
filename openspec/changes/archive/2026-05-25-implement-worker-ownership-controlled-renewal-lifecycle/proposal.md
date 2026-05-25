# Implement worker ownership controlled renewal lifecycle

## Summary

Add an explicit start/stop/status lifecycle to the worker ownership renewal supervisor while keeping the default runtime behavior disabled and fail-closed.

## Motivation

`renew_once(...)` proves one-shot lease renewal, but production readiness still needs an opt-in supervisor lifecycle that can be started, stopped, inspected, and quality-gated without enabling production worker ownership by default.

## Non-Goals

- Do not start the supervisor from app startup or SDK defaults.
- Do not enable production recovery ownership.
- Do not implement vendor-specific distributed locks.
- Do not enable recovery entry auto-claim.
- Do not change child executor dispatch.
