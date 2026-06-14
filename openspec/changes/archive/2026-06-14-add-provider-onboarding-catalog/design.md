## Context

MyPrivateAgent already supports several external provider families through `capability_runtime`: knowledge/RAG, ASR/TTS, OCR, layout, and document VLM. The previous stage added `/api/service-providers` so configured providers can be inspected and invoked explicitly.

The remaining gap is onboarding clarity. Setup details live across provider-specific docs and archived OpenSpec changes. Operators and future UI consumers need a single read-only catalog that explains which external projects are known, how they map to MyPrivateAgent capability ids, which environment variables enable them, and what checks prove they are ready.

## Goals / Non-Goals

**Goals:**

- Add a machine-readable provider onboarding catalog for known external provider families.
- Provide a compact readiness checklist per provider family.
- Link onboarding entries to `/api/service-providers`, `/api/capabilities`, and provider-specific docs.
- Make future external projects easier to attach by following the same catalog shape.

**Non-Goals:**

- Do not start provider services.
- Do not edit `.env`, provider repos, or secrets.
- Do not add a database-backed provider marketplace.
- Do not add new provider execution behavior beyond existing capability runtime.
- Do not promote default chat grounding, GraphRAG, voice default UX, OCR/VLM production default execution, or source binding automation.

## Decisions

1. **Use an in-code static catalog for the first slice.**

   The known provider families are stable enough to express as a deterministic read model. A database or user-managed marketplace would add migration, authorization, and lifecycle concerns that are not needed for this phase.

   Alternative considered: store provider onboarding entries in YAML. That may be useful later, but the current backend already keeps capability provider configuration in code/env and focused tests are simpler with a typed Python builder.

2. **Expose onboarding under `/api/provider-onboarding`.**

   This keeps it distinct from `/api/providers` model-provider configuration and `/api/service-providers` live provider management.

   Alternative considered: adding onboarding fields directly to `/api/service-providers`. That would make the live endpoint heavier and blur static setup guidance with runtime readiness.

3. **Keep catalog entries compact and non-secret.**

   Entries can list env var names, default local URLs, capability ids, docs, smoke commands, and boundaries, but never secret values or provider raw payloads.

4. **Use current configuration to compute checklist status.**

   The catalog can report whether required env toggles/base URLs appear configured in current process config, but it does not probe provider services. Live probing stays in `/api/service-providers` and `/api/capabilities/heartbeat`.

## Risks / Trade-offs

- [Risk] Static catalog can become stale as provider integrations evolve. -> Mitigation: add focused tests for key entries and document it as the canonical onboarding shape.
- [Risk] Operators may treat configured env as provider readiness. -> Mitigation: checklist items distinguish `config_ready` from `runtime_probe_required`.
- [Risk] Another provider API may confuse existing routes. -> Mitigation: use `/api/provider-onboarding` for static setup guidance and keep `/api/service-providers` for live readiness.

## Migration Plan

1. Add catalog service with first known provider entries.
2. Add read-only router endpoints.
3. Add focused tests for entry shape and route registration.
4. Sync docs and OpenSpec canonical specs.
