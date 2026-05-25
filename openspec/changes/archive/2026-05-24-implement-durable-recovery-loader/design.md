# Design

## Boundary

The loader turns durable workspace state into a recovery candidate. It does not execute recovery by itself; execution remains gated by checkpoint/resume cursor, registry binding, approval state, and worker ownership/retry policies.

## Required Flow

1. Read persisted run state from durable workspace backend.
2. Validate state contract and descriptor versions.
3. Rebuild compact SDK run snapshot, events, approval state, and continuation descriptors.
4. Resolve executable continuation only through `EmbeddedContinuationRegistry`.
5. Produce a recovery probe result with checkpoint, resume cursor, and operation boundary evidence.

## Failure Mode

Missing durable backend, stale descriptor, unresolved binding, resolved approval state, or unsafe payload shape must fail closed with machine-readable reason.

## Non-Goals

- No arbitrary callable deserialization.
- No hidden in-memory fallback for production recovery.
- No automatic retry scheduling.
