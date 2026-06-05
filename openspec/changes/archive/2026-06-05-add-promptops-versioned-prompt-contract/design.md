## Context

The current prompt layer is intentionally simple: `SystemPrompt` stores `prompt_key`, `prompt_type`, `content`, `priority`, `is_active`, `area`, and `tags`; `/api/learnings/prompts` exposes CRUD-style access; `RuntimeLearningService` and `PromptInjector` load active records directly. That is enough for early demos, but it does not give later grounding, eval, rollout, or rollback work a stable versioned contract.

Phase 21 should add a governance read model, not a heavy PromptOps platform. Existing records must remain valid, and chat behavior must not change.

## Goals / Non-Goals

**Goals:**

- Define a read-only versioned PromptOps contract over existing `SystemPrompt` records.
- Provide deterministic compatibility defaults for legacy prompts:
  - `version = "1"` unless a version tag is present.
  - `status = "active"` when `is_active` is true and no stronger status tag is present.
  - `status = "archived"` when `is_active` is false and no draft/review tag is present.
- Extract template variables from `{{variable_name}}` placeholders into a minimal JSON-schema-like object.
- Preserve optional governance references through bounded tag conventions such as `grounding_policy:<id>`, `eval_set:<id>`, `approval:<state>`, and `rollback_target:<version>`.
- Keep prompt injection and `/api/chat` unchanged.

**Non-Goals:**

- No prompt authoring studio.
- No approval automation.
- No rollout scheduler or gray release engine.
- No database migration or new prompt version table in this slice.
- No multi-turn eval runner.
- No automatic grounding enforcement.

## Decisions

1. **PromptOps starts as a compatibility read model.**
   - Decision: Add a service that converts existing `SystemPrompt` objects into `PromptOpsVersionContract` dictionaries.
   - Alternative considered: Add a dedicated `prompt_versions` table immediately.
   - Rationale: The current goal is lightweight trial readiness. A read model gives callers stable semantics without forcing a storage migration.

2. **Tags carry optional governance metadata for now.**
   - Decision: Use simple tag prefixes for version/status/owner/grounding/eval/approval/rollback metadata.
   - Alternative considered: Store a large JSON blob in `tags` or add columns.
   - Rationale: Existing records already have `tags`; prefix tags remain easy to inspect and compatible with current APIs.

3. **Runtime behavior remains unchanged.**
   - Decision: The PromptOps endpoint reports active/draft/review/archived state, but `RuntimeLearningService` continues to use current `is_active` filtering.
   - Alternative considered: Make runtime injection consume the new PromptOps active version contract.
   - Rationale: Behavior-affecting prompt rollout needs a later eval gate.

4. **Template variables are inferred, not validated against author input.**
   - Decision: Extract `{{name}}` placeholders from content and expose them as string variables.
   - Alternative considered: Require authors to provide a full JSON schema now.
   - Rationale: Inference gives useful visibility for legacy prompts while leaving explicit schema authoring for a later edit workflow.

## Risks / Trade-offs

- [Risk] Tag conventions are less robust than a normalized table. -> Mitigation: document this as the Phase 21 compatibility layer and keep the contract shape stable for a later storage migration.
- [Risk] `is_active=true` plus `status:draft` could confuse runtime behavior. -> Mitigation: status is governance-visible only in this slice; docs state runtime injection still follows existing `is_active` behavior.
- [Risk] Variable extraction misses non-mustache template styles. -> Mitigation: keep extraction narrow and deterministic; later PromptOps editing can add explicit schemas.

## Migration Plan

1. Add OpenSpec requirements for the PromptOps read model.
2. Implement a focused PromptOps contract service over `SystemPrompt`.
3. Add a read-only endpoint for contract/registry inspection.
4. Add focused tests for legacy defaults, tag metadata, variable extraction, and inactive prompt mapping.
5. Update roadmap and docs.
6. Validate and archive.

Rollback: remove the read-only service/endpoint and docs. Existing prompt CRUD and runtime injection remain unchanged.

## Open Questions

- Should the later durable prompt version store live in the learning schema or a separate runtime governance schema?
- Should activation become a controlled operation only after the multi-turn eval gate is available?
