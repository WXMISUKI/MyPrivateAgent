# Implement Child Executor Sandbox Backend Execution Seam

## Summary

Add an explicit opt-in sandbox child executor backend execution seam that can be called by the existing dispatcher in focused tests while default runtime behavior remains non-executing.

## Motivation

The previous slice proved that sandbox backend adapter readiness can be explicitly bound to a callable dispatcher adapter. The remaining gap is that the callable adapter is still hand-authored in tests instead of a reusable backend seam with consistent payload validation, compact attempt envelope output, audit/idempotency evidence, and fail-closed behavior.

This change provides that smallest executable seam without enabling production child executor dispatch.

## Scope

- Add an opt-in `SandboxChildExecutorBackend` or equivalent component.
- Validate compact dispatch payloads before execution.
- Return `build_sandbox_dispatch_attempt_envelope(...)` evidence for completed, blocked, and failed attempts.
- Preserve fail-closed behavior for unsafe payloads, missing required fields, missing idempotency, and handler failures.
- Wire runtime smoke and quality gates to prove the seam can be invoked only through explicit dispatcher setup.
- Keep default dispatch disabled and non-production.

## Non-Goals

- Do not start a background worker, queue, process sandbox, or remote executor.
- Do not enable child executor dispatch by default.
- Do not schedule child executor retry.
- Do not merge child output into the parent run.
- Do not change SDK recovery defaults or worker ownership behavior.

## Impact

- Backend contracts and focused tests for child executor sandbox backend and dispatcher.
- Runtime smoke, Quality Gate, Runtime Contract Gate, Snapshot, and health trace coverage.
- Canonical OpenSpec specs and runtime docs.
