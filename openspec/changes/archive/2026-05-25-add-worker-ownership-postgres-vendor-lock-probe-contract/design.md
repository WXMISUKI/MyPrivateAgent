## Context

The existing vendor lock adapter seam can describe capability readiness, but it has no backend-specific probe evidence. A future concrete implementation needs a place to record PostgreSQL advisory lock assumptions before any runtime path treats it as production-worthy.

## Goals / Non-Goals

**Goals:**
- Add a side-effect-free PostgreSQL advisory lock probe contract.
- Keep the default probe blocked and descriptive.
- Allow a future concrete adapter to pass probe readiness without changing the production gate shape.
- Keep SQL row lease/fencing separate from PostgreSQL advisory lock semantics.
- Guard the contract through smoke, Quality Gate, Runtime Contract Gate, docs, and specs.

**Non-Goals:**
- No PostgreSQL connection.
- No advisory lock acquire/renew/release execution.
- No migration or dependency addition.
- No production default ownership enablement.
- No default recovery auto-claim.
- No background supervisor startup.

## Decisions

- Add the probe builder in `worker_ownership.py` next to the vendor lock adapter contract builder.
- Embed probe evidence under `adapter_contract.backend_probe` so future backend families can follow the same pattern.
- Treat a ready probe as descriptive only. Production gate readiness still requires production lock allowment, target decision readiness, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, and explicit production enablement.
- Require explicit PostgreSQL semantics: advisory lock function family, lock key derivation, session or transaction scope, fencing token binding, TTL/renewal strategy, failover behavior, stale owner cleanup, and probe safety evidence.

## Risks / Trade-offs

- [Risk] A PostgreSQL-named contract may imply real DB behavior. -> Mitigation: the contract states `executes_probe = false` and gate evidence keeps production default disabled.
- [Risk] Backend-specific fields add summary noise. -> Mitigation: expose compact fields only under existing vendor lock adapter evidence.
- [Risk] Future PostgreSQL implementation may choose transaction locks instead of session locks. -> Mitigation: the probe records `lock_scope` and `advisory_lock_family` as explicit fields.
