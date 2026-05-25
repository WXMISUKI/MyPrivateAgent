## Context

The current worker ownership contract already exposes a side-effect-free `production_enablement_runtime_config_consumer`. It can normalize caller-owned runtime config or rollout artifact metadata into nested production default enablement input source and production gate composition dry-run evidence.

The remaining gap is assembly: runtime profile consumers currently see the consumer evidence produced by direct builder/default paths, but there is no explicit runtime factory input that carries caller-owned config through the same `RuntimeSurfaceService -> EmbeddedRuntimeFactory -> build_runtime_contract()` path used by governance tooling.

## Goals / Non-Goals

**Goals:**

- Add a narrow runtime factory input for worker ownership production enablement config evidence.
- Bind Runtime Surface effective config into the default embedded runtime factory without creating a new execution path.
- Keep no-config behavior blocked and observable.
- Let a complete local config dict produce ready descriptive evidence in Runtime Profile.
- Add focused tests and quality evidence for the binding.

**Non-Goals:**

- No production default worker ownership enablement.
- No PostgreSQL advisory lock execution.
- No background worker, renewal loop, timer, scheduler, or recovery auto-claim.
- No remote config reads or file loading.
- No database migration.
- No frontend UI expansion.

## Decisions

1. Store the binding on `EmbeddedRuntimeFactory`.

   The factory already owns runtime dependency contract assembly. Adding a constructor field or setter for `worker_ownership_production_enablement_config` keeps SDK, Facade, and Runtime Surface aligned with the default runtime dependency path.

   Alternative considered: have `RuntimeSurfaceService` call worker ownership builders directly. That would duplicate contract assembly and make Runtime Profile diverge from factory evidence.

2. Treat Runtime Surface config as caller-owned metadata only.

   The binding accepts an already materialized dict from effective runtime surface config. It must not read a path, remote source, secret store, or environment payload. This keeps the consumer descriptive and side-effect-free.

   Alternative considered: parse a config file or environment variable directly in the worker ownership module. That would blur config loading with contract building and increase production enablement risk.

3. Preserve fail-closed authorization semantics.

   Ready consumer evidence may appear in Runtime Profile, but `will_enable_production_default`, `executes_lock`, `starts_background_worker`, and `runs_recovery_auto_claim` remain false. Production authorization remains gated by existing production gate and future explicit enablement work.

## Risks / Trade-offs

- Config shape drift -> Mitigate with builder-level and Runtime Surface focused tests.
- Consumer readiness misread as authorization -> Mitigate with unchanged non-execution flags, docs, quality gate assertions, and Runtime Contract Gate summary naming.
- Runtime Surface config service grows too broad -> Mitigate by adding only a single optional key and keeping interpretation in worker ownership builder/factory.
- Existing dirty worktree interactions -> Mitigate by touching only this change's contract, tests, scripts, and docs.

## Migration Plan

No migration is required. Default behavior remains blocked when no config is supplied. Rollback is removing the optional config input; existing worker ownership contract defaults remain valid.

## Open Questions

None for this slice. Future production enablement remains a separate change.
