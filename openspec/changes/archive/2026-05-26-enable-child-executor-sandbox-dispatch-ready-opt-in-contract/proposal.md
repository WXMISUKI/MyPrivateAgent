# Enable Child Executor Sandbox Dispatch Ready Opt-in Contract

## Summary

Teach the side-effect-free child executor dispatch contract to report a ready sandbox dispatch boundary when all opt-in sandbox evidence is supplied, while default runtime construction remains blocked and non-executing.

## Motivation

The sandbox backend now has an explicit execution seam, and the dispatcher can invoke it when a caller hand-builds a ready dispatch contract. The remaining gap is that the canonical dispatch contract does not yet have a quality-gated ready sample proving that promotion, prerequisites, backend registry, sandbox binding, idempotency, and execution seam evidence compose into `dispatch_ready = true`.

This change closes that contract gap without starting a worker or making child executor dispatch a default SDK behavior.

## Scope

- Extend the child executor dispatch contract to accept opt-in sandbox execution seam evidence.
- Preserve fail-closed blockers for missing sandbox binding, missing execution seam support, missing idempotency, unsafe payloads, or backend registry readiness gaps.
- Add focused tests proving an opt-in sandbox contract can become `dispatch_ready = true` while `will_dispatch = false`.
- Extend runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot coverage with the opt-in ready evidence.
- Sync canonical specs and runtime docs.

## Non-Goals

- Do not enable child executor dispatch by default.
- Do not start a background worker, queue, sandbox process, or remote executor.
- Do not merge child output into parent state.
- Do not schedule child executor retry.
- Do not change worker ownership or recovery defaults.

## Impact

- Backend SDK dispatch contract builder.
- Runtime contract smoke and quality gate summary.
- Runtime Contract Gate and Snapshot required fields.
- Focused backend tests and OpenSpec/runtime docs.
