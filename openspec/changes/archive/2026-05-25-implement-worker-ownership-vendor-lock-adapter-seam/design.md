## Context

The production gate already explains vendor lock semantics, target decision, and target decision input source. The remaining production-readiness gap is the adapter seam itself: the runtime cannot yet represent an opt-in vendor lock adapter boundary with acquire/renew/release/probe capability evidence while keeping the default blocked.

## Goals / Non-Goals

**Goals:**
- Add a side-effect-free vendor lock adapter contract builder.
- Model the default adapter as absent/noop and blocked.
- Allow a future concrete adapter to provide capability evidence without changing the production gate shape.
- Keep SQL row lease/fencing separate from vendor-specific distributed lock semantics.
- Guard the contract through smoke, Quality Gate, Runtime Contract Gate, docs, and specs.

**Non-Goals:**
- No database-specific lock implementation.
- No lock acquisition side effects.
- No migration or dependency addition.
- No production default ownership enablement.
- No default recovery auto-claim.
- No background supervisor startup.

## Decisions

- Add the adapter seam inside `worker_ownership.py` rather than a new service module. This keeps the change contract-focused and aligned with existing builder patterns.
- Use a contract builder first, not a concrete protocol hierarchy. The current need is runtime evidence and quality gates; a concrete backend can be introduced later with its own OpenSpec slice.
- Keep readiness strict: adapter kind, target backend, lock scope, fencing, TTL/renewal, failover, stale cleanup, acquire/renew/release/probe support, and production allowment must all be present before the adapter seam can report ready.
- Always treat SQL row lease/fencing as non-vendor-lock authority.

## Risks / Trade-offs

- [Risk] More fields may make summaries noisier. -> Mitigation: embed them only under existing vendor lock sections and normalize through existing coverage.
- [Risk] A ready adapter seam could be mistaken for default production authorization. -> Mitigation: production lock allowment and production default enablement remain separate blockers with explicit tests.
- [Risk] Future concrete adapter semantics may differ by database. -> Mitigation: this slice records adapter capability evidence only; backend-specific behavior remains a later slice.
