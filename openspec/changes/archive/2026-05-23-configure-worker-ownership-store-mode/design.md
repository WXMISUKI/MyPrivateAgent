## Context

Worker ownership currently has two adapters: the safe in-memory default and an opt-in SQLAlchemy durable store. Runtime dependencies already carry `worker_ownership_store`, but `get_runtime_worker_ownership_store()` always returns the in-memory singleton. Operators need an explicit configuration boundary before a SQL-backed ownership store can be adopted in a production-like deployment.

## Goals / Non-Goals

**Goals:**

- Add a `WORKER_OWNERSHIP_STORE_MODE` configuration knob with conservative defaults.
- Allow default runtime dependencies to construct either in-memory or SQLAlchemy ownership stores.
- Make the selected ownership mode and source visible in the runtime factory contract.
- Preserve current default behavior when no environment variable is set.

**Non-Goals:**

- Do not enable SQL ownership by default.
- Do not add database-specific locking primitives or isolation tuning.
- Do not change SDK recovery semantics, descriptor ownership evidence rules, or automatic lease claim behavior.
- Do not add UI controls for this backend configuration in this slice.

## Decisions

- **Mirror embedded workspace store modes.** Use `memory_only`, `prefer_sql_with_fallback`, and `strict_sql` because maintainers already understand these runtime bootstrap semantics. Alternative considered: a boolean `ENABLE_SQL_WORKER_OWNERSHIP`, rejected because it would not express strict startup failure versus fallback behavior.
- **Default to `memory_only`.** Ownership gates are safety-sensitive. A durable store should be intentionally enabled after schema migration and deployment checks. Alternative considered: derive SQL mode from `DB_MODE`, rejected because it would change existing runtime behavior too aggressively.
- **Construct the SQL ownership store in `worker_ownership.py`.** This keeps ownership-specific bootstrap close to the ownership adapter while avoiding circular dependency with runtime dependency assembly. Alternative considered: moving ownership construction into `adapters.py`, deferred because the ownership module already owns the singleton getter.
- **Fail closed for `strict_sql`, fallback for `prefer_sql_with_fallback`.** Strict mode raises if SQL bootstrap fails. Fallback mode returns in-memory ownership and marks mode evidence as fallback-active through the selected adapter contract.

## Risks / Trade-offs

- **Fallback may hide SQL ownership unavailability** -> Runtime contract exposes configured mode, actual adapter kind, durability, and mode source so consumers can detect memory fallback.
- **Default remains non-durable** -> This is intentional to avoid surprise behavior; production deployments must explicitly set the mode.
- **SQL construction depends on DB metadata availability** -> Bootstrap will call `Base.metadata.create_all(bind=engine)` like the existing workspace store path, and tests verify strict failure behavior.
