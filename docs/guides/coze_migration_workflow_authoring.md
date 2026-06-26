# Coze Workflow Migration Authoring Guide

This guide defines how teams migrate Coze workflows into MyPrivateAgent without creating scattered runtime entrypoints.

## Standard Directory

Every migrated workflow lives under:

```text
backend/coze_workflows/<workflow_id>/
```

Use one directory per workflow. Do not put multiple workflows in one directory.

Required structure:

```text
backend/coze_workflows/<workflow_id>/
  workflow.yaml
  prompts/
    system.md
    task.md
  examples/
    sample_input.xlsx
    expected_output.json
  source/
    coze_export/
      MANIFEST.yml
      workflow/
  README.md
```

## Manifest Is The Registry Entry

`workflow.yaml` is the only registration source. A workflow is not considered migrated until this file exists and declares:

- `id`
- `name`
- `version`
- `status`
- `owner`
- `source`
- `entrypoint`
- `inputs`
- `outputs`
- `prompts`
- `dependencies`
- `governance`
- `acceptance`

Do not register workflows with ad hoc Python imports, local scripts, or custom API routes.

## Capability Id

Workflow capability ids use:

```text
coze.workflow.<workflow_id>
```

Example:

```text
coze.workflow.hazardous_project_list_recognition
```

The capability id is the stable handle for future model calls, tests, governance views, and external orchestration.

## Status Lifecycle

- `draft`: asset exists, not callable by default
- `review`: ready for registry and acceptance review
- `active`: callable only after readiness and validation pass
- `deprecated`: kept for compatibility
- `archived`: retained as historical evidence

New migrations should start as `draft` or `review`. Do not mark a workflow `active` until dependencies, prompts, acceptance examples, and runtime behavior are verified.

## Dependency Declaration

All dependencies must be explicit in `workflow.yaml`.

For document and spreadsheet workflows, prefer managed capability names:

- `document.file_type.detect`
- `spreadsheet.table.extract`
- `llm.structured_json.generate`
- `json_schema.validate`

Do not keep Coze plugin names as runtime dependencies unless they are wrapped by a MyPrivateAgent provider or MCP capability.

## Prompt Migration

Move Coze prompt content into prompt files:

- `prompts/system.md`
- `prompts/task.md`

Keep original Coze exports in `source/coze_export/` for audit. The prompt files are the maintainable version used by MyPrivateAgent.

## Acceptance Examples

Each workflow should include at least one fixture and expected result:

```text
examples/<case>.xlsx
examples/<case>_expected.json
```

The expected result should be compact and deterministic enough for review. If a live model is required, mark `acceptance.smoke.live_model_required = true`.

## Collaboration Rules

- Each workflow has a primary owner and reviewers.
- Owners may edit only their workflow directory unless a shared runtime contract change is agreed.
- Cross-workflow direct imports are not allowed.
- Shared behavior must move into capability runtime, ToolRuntime, MCP Runtime, Skill Runtime, or a documented shared service.
- Production rollout requires registry readiness, acceptance evidence, and governance trace support.

## First Sample

The first real sample is:

```text
backend/coze_workflows/hazardous_project_list_recognition/
```

It migrates a Coze workflow that reads a dangerous construction project checklist and returns normalized JSON.
