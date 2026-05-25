# harden-worker-ownership-operations

## Why

Worker ownership currently has an in-memory seam, SQLAlchemy adapter, store mode, and runtime contract coverage. Production operation still needs explicit lease renewal, vendor lock posture, recovery-entry claim semantics, and rollout/migration guardrails.

## What Changes

- Add worker ownership operational readiness contract.
- Define heartbeat/renewal expectations and stale lease handling.
- Define recovery-entry automatic claim behavior behind explicit configuration.
- Add migration/rollout checklist evidence.

## Impact

- 收口对象：worker ownership store/service, runtime dependencies/factory contract, recovery gate integration, docs/specs/tests.
- 非目标：不 silently enable ownership enforcement for all runtimes；不 replace existing compact ownership evidence shape。
