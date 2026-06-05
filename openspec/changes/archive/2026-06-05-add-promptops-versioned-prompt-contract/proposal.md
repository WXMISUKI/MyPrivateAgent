## Why

MyPrivateAgent already has `/prompts` CRUD and runtime prompt injection, but prompts are still managed as mutable records rather than versioned runtime contracts. After grounding policy is visible, prompt activation now needs a lightweight PromptOps contract so future eval, rollback, and behavior promotion can refer to stable prompt versions.

## What Changes

- Add a versioned PromptOps contract that normalizes existing `SystemPrompt` records into governance-visible prompt versions.
- Preserve the existing `/prompts` CRUD and runtime injection behavior.
- Add a read-only PromptOps registry surface for prompt key, version, status, template variables, grounding policy reference, eval set reference, approval state, rollout metadata, and rollback target.
- Update roadmap and architecture docs to mark grounding policy as complete and PromptOps as the current Phase 21 slice.
- Non-goals:
  - Do not build a Prompt Studio UI.
  - Do not add prompt approval workflow automation.
  - Do not change default `/api/chat` prompt selection or runtime injection behavior.
  - Do not implement multi-turn eval, MemoryOps, gray release automation, or provider-side RAG work in this change.
  - Do not add new runtime dependencies or database migrations unless the existing model cannot support the read-only contract.

## Capabilities

### New Capabilities

- `promptops-versioned-prompt-contract`: Defines the minimal versioned PromptOps read model and compatibility mapping from existing prompt records.

### Modified Capabilities

- `runtime-surface-contract-assembler`: Runtime contract documentation can reference PromptOps visibility as governance metadata, without requiring chat behavior changes.

## Impact

- Affected backend contracts:
  - `backend/models.py` existing `SystemPrompt` remains the persistence source.
  - `backend/routers/learnings.py` exposes a read-only PromptOps contract endpoint.
  - New focused service for normalizing prompt records into PromptOps entries.
- Affected docs:
  - `docs/roadmap/internal_agent_control_tasks_2026-06-03.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/guides/domain_agent_development_guide.md`
- Affected tests:
  - focused backend tests for PromptOps normalization and compatibility behavior.
- Dependencies:
  - No new runtime dependency.
  - No external provider dependency.
