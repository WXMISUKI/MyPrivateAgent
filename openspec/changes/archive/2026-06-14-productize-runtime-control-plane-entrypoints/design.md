## Context

The project has reached a point where the important question is no longer "does a provider or trial surface exist?" but "which seam should a maintainer or external project use first?" Provider onboarding now has catalog, service-provider management, UI surface, and acceptance gate. Domain agent trial, Embedded SDK, and framework adapter paths also have stable boundary docs.

The documentation entrypoint should now behave like a control-plane product surface: concise, task-oriented, and explicit about gated behavior.

## Goals / Non-Goals

**Goals:**

- Make `docs/README.md` the first useful entrypoint for current architecture and integration paths.
- Keep `agent_runtime_control_plane_entrypoint.md` as the detailed architecture start page.
- Keep `project_entrypoint_checklist.md` as the operator checklist.
- Surface provider acceptance gate, Embedded SDK, framework adapter, and domain-agent boundaries.

**Non-Goals:**

- No runtime code changes.
- No new API routes.
- No UI changes.
- No behavior promotion.
- No docs archive cleanup or historical doc rewrite.

## Decisions

1. **Use existing entrypoint files instead of adding another document.**
   The repo already has `agent_runtime_control_plane_entrypoint.md` and `project_entrypoint_checklist.md`. Adding a third entrypoint would increase confusion.

2. **Make `docs/README.md` route by task.**
   A new maintainer usually arrives with a goal, not a contract name. The README should map tasks to documents and verification commands.

3. **Keep historical docs secondary.**
   `docs/change` and older planning documents remain useful audit trails, but the entrypoint should not require reading them first.

## Risks / Trade-offs

- [Risk] Documentation can drift from code. -> Mitigation: tie entrypoint docs to canonical specs and strict OpenSpec validation.
- [Risk] Entry docs become too long. -> Mitigation: keep the top section task-oriented and link to deeper documents.
- [Risk] Readers confuse explicit readiness with default runtime behavior. -> Mitigation: repeat ready/gated/non-goal boundaries in the entrypoint matrix.
