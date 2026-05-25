# Change: Add Worker Ownership PostgreSQL Rollout Artifact Consumer

## Summary

Add a read-only worker ownership rollout artifact/config consumer that can normalize PostgreSQL advisory lock rollout evidence into the existing production default enablement input source contract. The consumer proves whether an explicit rollout artifact is complete enough to serve as enablement evidence while keeping production default ownership disabled and advisory lock execution opt-in.

## Motivation

Worker ownership now has a PostgreSQL advisory lock execution seam and a production default enablement input source. The next safety gap is the bridge between an operator artifact/config payload and those contracts. Without a normalized consumer, a future default enablement request would still require ad hoc interpretation of artifact fields.

## Scope

- Add a read-only rollout artifact/config consumer contract for PostgreSQL advisory lock enablement evidence.
- Produce a nested `production_default_enablement_input_source` when the artifact is complete.
- Surface consumer evidence through worker ownership runtime smoke, Quality Gate, and Runtime Contract Gate coverage.
- Keep default runtime posture blocked, descriptive, and non-executing.
- Update canonical specs and project docs.

## Non-Goals

- No production default worker ownership enablement.
- No automatic rollout execution.
- No file-system artifact loader or remote config fetcher.
- No PostgreSQL connection or advisory lock execution from the consumer.
- No recovery entry auto-claim enablement.
- No API endpoint, migration, or SDK default behavior change.
