# Coze Workflow Migration Assets

This directory is the standard home for Coze workflow migrations.

Each migrated workflow MUST live in its own directory:

```text
backend/coze_workflows/<workflow_id>/
  workflow.yaml
  prompts/
    system.md
    task.md
  examples/
    happy_path.json
  README.md
```

## Workflow Id

- Use a stable machine id such as `customer_intake`.
- Prefer `snake_case` for Python-friendly paths.
- Do not rename a workflow id after other agents or capabilities reference it.

## Ownership

Each workflow directory has one primary owner in `workflow.yaml`.

The owner is responsible for:

- keeping the migrated Coze prompt assets current
- declaring all tool, MCP, Skill, provider, and knowledge-source dependencies
- maintaining acceptance examples
- updating workflow status during review and rollout

## Required Files

- `workflow.yaml`: the only registry entrypoint for the workflow
- `prompts/*.md`: prompt bodies referenced by the manifest
- `examples/*.json`: acceptance examples used by smoke tests and review
- `README.md`: short human-facing notes for maintainers

Prompt bodies MUST be kept in prompt files, not embedded directly in `workflow.yaml`.

## Status Lifecycle

Supported statuses:

- `draft`: visible to maintainers, not callable by default
- `review`: ready for review, not production callable by default
- `active`: callable only when readiness checks pass
- `deprecated`: kept for compatibility, new callers should not use it
- `archived`: historical asset, not callable

## Dependency Rules

Every runtime dependency MUST be declared in `workflow.yaml`:

- `dependencies.tools`
- `dependencies.mcp_capabilities`
- `dependencies.skills`
- `dependencies.providers`
- `dependencies.knowledge_sources`

Hidden dependencies are not allowed. If a workflow implementation needs an undeclared capability, the workflow is not production-ready.

## Invocation Rules

Do not import another workflow directory implementation directly.

Supported callers MUST use the unified workflow or capability runtime entrypoint once implemented. This keeps permissions, run identity, trace, audit, and errors consistent.

## Template

Start new migrations from:

```text
backend/coze_workflows/_template/workflow.yaml
```

The `_template` directory is for authoring only and MUST NOT be treated as a callable workflow.
