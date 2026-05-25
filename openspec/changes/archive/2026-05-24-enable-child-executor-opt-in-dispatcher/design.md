# Design

## Boundary

The dispatcher is a separate opt-in implementation behind the existing child executor dispatch contract. It must never infer readiness from `delegate_run(...)` alone.

## Required Flow

1. Build or read `child_executor_dispatch_contract`.
2. Require `dispatch_ready = true`.
3. Require selected backend registry entry with `dispatch_ready = true`.
4. Require execution prerequisites `ready = true`.
5. Dispatch through a registered backend adapter.
6. Record compact dispatch evidence on child run metadata and runtime trace.

## Failure Mode

Any missing contract, blocked gate, unknown backend, stale readiness, adapter error, or missing sandbox configuration must fail closed and produce compact audit evidence.

## Non-Goals

- No default background worker pool.
- No scheduler fan-out rewrite.
- No unbounded payload copying into trace.
