---
name: coze-workflow-migration
description: Provides a repeatable workflow for migrating Coze workflows into MyPrivateAgent with asset authoring, read-only registry validation, runtime surface promotion, capability exposure, invocation checks, and go-live acceptance. Use when teams migrate Coze workflows into backend/coze_workflows, need end-to-end test and launch checklists, or want a shared authoring standard for multi-person migration work.
---

# Coze Workflow Migration

## Quick Start

1. Put each workflow under `backend/coze_workflows/<workflow_id>/`.
2. Keep prompt bodies in `prompts/*.md` and reference them from `workflow.yaml`.
3. Use the sample guide in [docs/guides/coze_migration_workflow_authoring.md](../../../docs/guides/coze_migration_workflow_authoring.md) as the authoring baseline.
4. Keep the migration contract aligned with [openspec/changes/define-coze-migration-capability-runtime/tasks.md](../../../openspec/changes/define-coze-migration-capability-runtime/tasks.md).
5. Treat `status: review` as non-callable by default; only promote to `active` after launch evidence is complete.

## End-to-End Flow

1. Author assets under one workflow directory.
2. Validate `workflow.yaml`, prompt references, and acceptance fixtures.
3. Confirm the read-only registry reports the expected readiness and blockers.
4. Expose the workflow through runtime surface and capability contracts.
5. Verify invoke boundaries only after registry and capability checks pass.
6. Run launch acceptance and capture evidence before any `active` promotion.

## Workflow Patterns

### Spreadsheet Recognition

- Typical input: `file`
- Typical output: normalized JSON records
- Typical smoke focus: row count, field mapping, and blocked dependency handling

### Route Orchestration

- Typical input: `user_input` plus optional `data[]` candidate list
- Typical output: `command`, `params`, and `message`
- Typical smoke focus: single-match routing, square-page routing, multi-match clarification, and no-match clarification
- If the route workflow uses HTTP steps in the original Coze export, keep the original intent in `source.migration_notes` and make sure the runtime capability list matches the actual executor support before promotion

## Recommended Validation Sequence

1. Check `backend/coze_workflows/<workflow_id>/workflow.yaml` exists and is parseable.
2. Confirm `prompts/system.md` and `prompts/task.md` exist and are referenced by manifest.
3. Confirm every `acceptance.examples[*].expected_path` file exists.
4. Run the registry inspection path first and confirm it stays side-effect free.
5. If the workflow is still `review`, expect invoke to fail closed with `COZE_WORKFLOW_BLOCKED`.
6. If the workflow is `active` and ready, run a real fixture-based invoke and compare the structured JSON output to the expected example.
7. Record the smoke result, blocker reason, and promotion decision in docs or change notes.
8. For route workflows, verify the returned command set matches the scenario matrix before treating the workflow as a shared template.

## Operating Rules

- Treat `workflow.yaml` as the only registration source.
- Do not import one workflow directory directly from another.
- Keep the registry side-effect free until the explicit invoke slice is approved.
- Prefer `draft` or `review` while migration evidence is still being collected.
- Promote to `active` only after prompts, dependencies, examples, and trace expectations are verified.
- Keep launch evidence stable: same fixture, same expected JSON, same structured error codes for blocked states.
- For route workflows, keep `route_agent`, `route_square`, `clarify_multi`, and `clarify_none` examples in the acceptance matrix when they are part of the original business behavior.

## Test And Launch Checklist

1. Confirm the workflow directory exists and contains `workflow.yaml`.
2. Confirm `prompts/system.md`, `prompts/task.md`, and acceptance example files exist.
3. Run the registry read-only contract check.
4. Verify domain agent references, capability exposure, and invoke envelope alignment.
5. For `review` workflows, verify blocked cases fail closed with stable error codes.
6. For `active` workflows, run a real end-to-end smoke test against a representative fixture and compare the response to the expected JSON.
7. Record go-live evidence in docs and OpenSpec tasks.

## References

- [REFERENCE.md](REFERENCE.md)
- [EXAMPLES.md](EXAMPLES.md)
