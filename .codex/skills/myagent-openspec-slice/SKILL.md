---
name: myagent-openspec-slice
description: Choose the next smallest safe development slice for MyPrivateAgent. Use when the user asks what to improve next, says continue improving, asks to inspect roadmap/spec/docs, or wants a backend/frontend optimization direction before implementation.
---

# MyPrivateAgent OpenSpec Slice

Use this skill to decide the next development slice without relying on conversation memory.

## Workflow

1. Rebuild current context from project truth sources before recommending work:
   - `docs/roadmap/next_phase_hardening.md`
   - `docs/architecture/runtime_contracts.md`
   - `openspec/specs/`
   - `openspec/changes/` and `openspec/changes/archive/`
2. Check active OpenSpec changes:
   - `openspec list --json`
   - If there is one relevant active change, continue it.
   - If none exists but a canonical spec already covers the work, use the canonical spec as the guardrail.
   - If the work changes runtime contract, read model, governance semantics, or external API shape and no spec/change covers it, create or propose a focused OpenSpec change first.
3. Select a slice that is small enough to verify in one focused test command.
4. State the slice using:
   - Current phase or module.
   - Why this is the next best step.
   - Affected code paths.
   - Affected docs/specs.
   - Minimal verification command.
5. Prefer backend contract/read-model convergence over frontend polish unless the frontend work reduces maintenance risk or exposes an existing contract.

## Slice Rules

- Prefer one concern per slice: contract builder, read model, quality gate, UI region, or docs alignment.
- Do not mix backend contract changes with broad UI redesign unless necessary.
- Do not open a new OpenSpec change for a tiny implementation-only follow-up already covered by a canonical spec.
- Do create a change when semantics are new, contract shape changes, or the user is still clarifying requirements.
- If the repo is dirty, ignore unrelated changes and avoid reverting user work.

## Completion Criteria

- The chosen slice has a concrete implementation target.
- Focused tests or validation commands are named.
- Docs/spec sync requirements are explicit.
- The recommendation can be executed immediately without another planning loop.
