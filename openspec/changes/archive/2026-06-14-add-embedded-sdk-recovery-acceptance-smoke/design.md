## Context

The project has already implemented the core Embedded SDK recovery seams: workspace persistence posture, continuation descriptors, registry-backed reattachment, approval submission, and `resume_run(..., continue_loop=True)`. The current gap is operational confidence for explicit consumers. A caller can read individual tests or runtime smoke output, but there is no compact acceptance pack that answers: "Can this embedded recovery path be consumed now, and what exactly remains gated?"

This design keeps the slice deliberately small. It packages existing SDK behavior into deterministic evidence and leaves production recovery enablement to existing gates.

## Goals / Non-Goals

**Goals:**

- Provide a JSON evidence contract named `embedded-sdk-recovery-acceptance-smoke-v1`.
- Prove the accepted path by running a durable workspace and registry-backed recovery scenario through create, execute, probe, approve, and resume.
- Prove blocked paths for memory-only workspace and missing registry binding.
- Keep evidence compact, machine-readable, and free of executable objects.
- Add a script that can be used by maintainers or future quality gates without calling real providers or chat.

**Non-Goals:**

- No worker lease, production worker ownership, background auto-recovery, or distributed executor.
- No real LLM, model provider call, default `/api/chat` change, or final answer policy change.
- No new persistence backend, database migration, or broad SDK refactor.
- No provider capability invocation or unifiedKnowledgeRAG behavior change.

## Decisions

1. Add a dedicated acceptance service rather than extending `runtime_contract_smoke.py`.

   Rationale: `runtime_contract_smoke.py` is already broad and optimized for contract gate aggregation. A dedicated service keeps this slice consumable by SDK users and future provider-style onboarding without coupling it to the full runtime smoke.

   Alternative considered: add only another runtime contract smoke check. Rejected because it would still leave no focused script or acceptance evidence shape for explicit embedded consumers.

2. Use controlled SDK scenarios built from existing workspace and registry seams.

   Rationale: The acceptance pack should exercise the actual public Embedded SDK/facade recovery path, not a parallel simulator. The service can still use a small durable test store subclass or SQLite-backed store depending on the existing local pattern.

   Alternative considered: inspect contracts only. Rejected because acceptance should prove create/execute/probe/approve/resume behavior, not just metadata presence.

3. Fail closed on memory-only and missing registry binding.

   Rationale: A memory backend can prove in-process preview behavior, but it must not be presented as durable cross-process recovery acceptance. A missing registry binding means the persisted descriptor cannot be safely reattached.

   Alternative considered: warn but accept memory preview. Rejected because it would blur runtime preview with explicit durable consumption readiness.

4. Output sanitized compact evidence.

   Rationale: The evidence may be archived, pasted into issues, or consumed by quality gates. It must not leak callables, provider clients, stream objects, or raw execution internals.

   Alternative considered: return the full SDK payload. Rejected because SDK payloads can contain richer runtime internals than an acceptance gate needs.

## Risks / Trade-offs

- Acceptance smoke duplicates part of existing facade tests -> Keep it as an operational evidence pack with explicit decisions and script exit codes.
- Durable scenario may become too heavy if it depends on a real external database -> Use only local deterministic stores and existing SQLAlchemy test utilities if needed.
- Consumers may overread `accepted` as production auto-recovery -> Evidence and docs must state that accepted means explicit embedded consumption only.
- Sanitization could hide debugging detail -> Preserve compact blockers, warnings, entrypoints, binding ids, and recovery reasons while excluding executable objects.

## Migration Plan

No runtime migration is required. The change adds a service, script, focused tests, canonical specs, and docs. Rollback is removal of the new service/script/docs/spec addition without touching SDK behavior.

## Open Questions

None for this slice. Production auto-recovery, worker ownership, retry scheduling, and real executor wiring remain separate future changes.
