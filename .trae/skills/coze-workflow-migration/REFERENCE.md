# Coze Workflow Migration Reference

## What This Skill Covers

- Workflow authoring under `backend/coze_workflows/<workflow_id>/`
- Registry validation
- Dependency resolution
- Capability promotion
- Invocation checks
- Launch acceptance

## Checklist Summary

1. Identify the workflow type.
2. Create the directory layout.
3. Write `workflow.yaml`.
4. Declare dependencies.
5. Migrate prompts.
6. Add acceptance fixtures.
7. Run registry and invocation checks.
8. Publish launch acceptance evidence.

## Dependency Notes

- Spreadsheet workflows typically use:
  - `document.file_type.detect`
  - `spreadsheet.table.extract`
  - `llm.structured_json.generate`
  - `json_schema.validate`
- Route workflows may use `http.request` only when the runtime actually supports it.
- If a dependency is missing, surface it immediately and either resolve it or keep the workflow blocked.

## Acceptance Notes

- Spreadsheet workflows should show row count, field normalization, category mapping, and dependency blockers.
- Route workflows should show the full scenario matrix:
  - single match
  - square-page jump
  - multi-match clarification
  - no-match clarification
- Always publish a `docs/integration/<workflow>-launch-acceptance` record for handoff.

