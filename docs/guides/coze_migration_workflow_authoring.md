# Coze Workflow Migration Authoring Guide

This guide defines how teams migrate Coze workflows into MyPrivateAgent without creating scattered runtime entrypoints.

## Migration Roadmap

1. Read the original Coze export and identify the workflow type.
2. Decide whether the workflow is a spreadsheet extractor, route orchestrator, or another capability pattern.
3. Create a single workflow directory under `backend/coze_workflows/<workflow_id>/`.
4. Write `workflow.yaml` as the only registration source.
5. Move prompt text into `prompts/system.md` and `prompts/task.md`.
6. Add deterministic acceptance fixtures under `examples/`.
7. Run the registry read-only contract check.
8. Resolve missing dependencies or document blockers explicitly.
9. Promote to `active` only after invoke and smoke evidence both pass.
10. Publish a `docs/integration/*-launch-acceptance` record for team reuse.
11. Use the Workflow Lab verification runbook for backend, frontend, and replay checks.

## Workflow Lab Usage

After the workflow is registered, use the Workflow Lab to verify the migration before treating it as reusable.

1. Open the workflow list and confirm the workflow appears with the expected status, readiness, owner, capability id, and launch evidence.
2. Open the workflow detail and inspect input schema, output schema, prompt metadata, governance, and dependency mapping.
3. Replay each acceptance example through the lab invocation action.
4. Compare the returned JSON against the expected fixture.
5. If the replay is blocked, record the blocker and keep the workflow in `draft` or `review` until the blocker is resolved.
6. Keep Workflow Lab separate from default chat and provider settings. It is a migration verification surface, not a user-facing execution entrypoint.
7. Treat dependency mapping as the migration truth source. Each node should be classified as `runtime_capability`, `provider_backed`, `artifact_input`, or `explicit_blocker` before the workflow is promoted.

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

The `source/coze_export/` directory is the audit trail. The `workflow.yaml`, prompts, examples, and README are the maintainable project assets.

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

If the original Coze export contains behavior that is not supported by the current runtime, keep the manifest honest. Do not pretend a capability exists just to make the registry green.

When the registry shows a gap, surface it in Workflow Lab dependency mapping so reviewers can see whether the node maps to a local capability, a provider-backed capability, an artifact input, or an explicit blocker.

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

For route workflows, `active` means the scenario matrix has been exercised and the returned command contract is stable.

## Dependency Declaration

All dependencies must be explicit in `workflow.yaml`.

For document and spreadsheet workflows, prefer managed capability names:

- `document.file_type.detect`
- `spreadsheet.table.extract`
- `llm.structured_json.generate`
- `json_schema.validate`

Do not keep Coze plugin names as runtime dependencies unless they are wrapped by a MyPrivateAgent provider or MCP capability.

### Missing Capability Handling

If a workflow references a capability that the project does not currently support, do not silently skip it.

1. Surface the missing capability clearly in the registry or smoke result.
2. Try to map it to an existing supported capability or shared service when that is the intended runtime behavior.
3. If the project needs the capability, add the executor or contract support explicitly and re-run the validation.
4. If the gap cannot be closed yet, keep the workflow blocked or draft and document the blocker in the acceptance notes.

Typical examples:

- Spreadsheet workflows usually depend on `document.file_type.detect`, `spreadsheet.table.extract`, `llm.structured_json.generate`, and `json_schema.validate`.
- Route workflows may depend on `http.request` if the runtime is expected to support route-capability compatibility, but they can also be implemented with deterministic local routing rules when that matches the current contract.
- If a dependency is missing in a future migration, call it out immediately and do not bury it inside a passing test log.

Dependency mapping example:

- `http.request` -> `kind: runtime_capability`, `status: ready`, `target_capability_id: http.request`
- `llm.structured_json.generate` -> `kind: runtime_capability`, `status: ready`
- Provider-backed capabilities -> `kind: provider_backed`, include `provider_id`, `onboarding_path`, and `service_provider_detail_path`
- `inputs.file` -> `kind: artifact_input`, accepted reference types `content_ref`, `artifact_id`, `runtime_file_ref`
- Unsupported Coze node -> `kind: explicit_blocker`, include a machine-readable blocker reason

Promoted workflows are invoked through the stable capability contract `coze.workflow.<workflow_id>`. The invoke envelope should preserve `workflow_id`, `capability_id`, `workflow_version`, `run_id`, `status`, `authorization`, `invocation_policy`, and `trace_summary`, and draft/review workflows must fail closed.

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

For route workflows, acceptance should include:

- single-match routing
- collection/square-page routing
- multi-match clarification
- no-match clarification

For spreadsheet workflows, acceptance should include:

- row count
- field normalization
- category mapping
- blocked dependency handling

If the workflow needs a live model or an external capability, the acceptance record should say so explicitly.

## Collaboration Rules

- Each workflow has a primary owner and reviewers.
- Owners may edit only their workflow directory unless a shared runtime contract change is agreed.
- Cross-workflow direct imports are not allowed.
- Shared behavior must move into capability runtime, ToolRuntime, MCP Runtime, Skill Runtime, or a documented shared service.
- Production rollout requires registry readiness, acceptance evidence, and governance trace support.
- Teams should publish a `docs/integration/<workflow>-launch-acceptance` record so the next contributor can replay the same input/output matrix.
- When a missing capability is discovered, the implementation notes should say what was missing, what was attempted, and why the issue was left blocked or resolved.
- When possible, reference the Workflow Lab replay result in the launch acceptance record so the fixture, returned JSON, and capability envelope stay tied together.

## First Sample

The first real sample is:

```text
backend/coze_workflows/hazardous_project_list_recognition/
```

It migrates a Coze workflow that reads a dangerous construction project checklist and returns normalized JSON.

## Route Workflow Example

```text
backend/coze_workflows/szzg_agent_encapsulation_route/
```

It migrates a Coze routing workflow that resolves agent jumps and square-page jumps through a stable `command + params + message` contract.
