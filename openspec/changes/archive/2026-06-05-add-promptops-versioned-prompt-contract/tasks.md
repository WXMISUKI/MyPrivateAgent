## 1. Specification

- [x] 1.1 Validate proposal/design/specs for Phase 21 PromptOps scope and non-goals.
- [x] 1.2 Confirm the new `promptops-versioned-prompt-contract` capability keeps existing prompt CRUD and chat behavior stable.
- [x] 1.3 Confirm the Runtime Surface/runtime contract delta is visibility-only.

## 2. Backend Contract

- [x] 2.1 Add a focused PromptOps contract service that normalizes existing `SystemPrompt` records.
- [x] 2.2 Expose legacy compatibility defaults for version, status, runtime binding, and variables schema.
- [x] 2.3 Preserve tag-derived governance metadata for owner, grounding policy, eval set, approval state, rollout strategy, and rollback target.
- [x] 2.4 Add a read-only PromptOps registry endpoint without changing prompt injection or `/api/chat`.

## 3. Documentation

- [x] 3.1 Update the internal control roadmap to mark grounding policy complete and PromptOps as Phase 21 current work.
- [x] 3.2 Document the PromptOps contract in runtime contracts.
- [x] 3.3 Update the domain agent guide with lightweight PromptOps tag conventions and behavior boundaries.

## 4. Verification

- [x] 4.1 Add focused tests for legacy prompt normalization, explicit tag metadata, template variables, and inactive prompt status.
- [x] 4.2 Run focused PromptOps tests.
- [x] 4.3 Run `openspec validate add-promptops-versioned-prompt-contract --strict`.
- [x] 4.4 Run `openspec validate --all --strict`.

## 5. Archive

- [x] 5.1 Sync final PromptOps decisions to canonical specs.
- [x] 5.2 Archive the change after implementation tasks are complete.
