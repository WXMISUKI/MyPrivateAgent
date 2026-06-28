---
name: coze-workflow-migration
description: Checklist-style migration skill for moving Coze workflows into MyPrivateAgent with asset authoring, dependency resolution, registry validation, capability promotion, invocation checks, and launch acceptance. Use when teams need a repeatable, step-by-step workflow for spreadsheet, route, or other Coze migration patterns under backend/coze_workflows.
---

# Coze Workflow Migration Checklist

## 0. Use This Skill When

- You are migrating a Coze workflow into `backend/coze_workflows/<workflow_id>/`.
- You need to keep the registry contract, runtime dependency contract, and acceptance evidence aligned.
- You want a repeatable checklist for spreadsheet workflows, route workflows, or other workflow patterns.
- You need to verify launch readiness without silently skipping missing dependencies.

## 1. Before You Start

- Read the original Coze export and identify the workflow type.
- Confirm whether the workflow is mainly:
  - spreadsheet recognition
  - route orchestration
  - another capability pattern
- Decide the intended runtime behavior before editing files.
- If the workflow needs a capability the project does not support yet, stop and mark that dependency explicitly.

## 2. Create The Workflow Directory

- Create exactly one directory under `backend/coze_workflows/<workflow_id>/`.
- Do not place multiple workflows in one directory.
- Keep the original export under `source/coze_export/` when available.
- Treat the original export as audit evidence, not as the maintainable runtime asset.

Required layout:

```text
backend/coze_workflows/<workflow_id>/
  workflow.yaml
  prompts/
    system.md
    task.md
  examples/
    <case>.json
    <case>_expected.json
  source/
    coze_export/
      MANIFEST.yml
      workflow/
  README.md
```

## 3. Write The Manifest

- Use `workflow.yaml` as the only registration source.
- Do not register workflows with ad hoc Python imports, custom routes, or local scripts.
- Keep the manifest honest about unsupported behavior.
- Use stable capability ids in the form `coze.workflow.<workflow_id>`.

Checklist:

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

## 4. Set The Status Correctly

- `draft` means asset exists but is not callable by default.
- `review` means ready for registry and acceptance review.
- `active` means callable only after readiness and validation pass.
- `deprecated` means kept for compatibility.
- `archived` means retained as historical evidence.

Rules:

- Start new work as `draft` or `review`.
- Do not mark a workflow `active` until dependencies, prompts, acceptance examples, and runtime behavior are verified.
- For route workflows, `active` means the scenario matrix has been exercised and the returned command contract is stable.

## 5. Declare Dependencies

- Declare every dependency explicitly in `workflow.yaml`.
- For spreadsheet workflows, prefer managed capability names:
  - `document.file_type.detect`
  - `spreadsheet.table.extract`
  - `llm.structured_json.generate`
  - `json_schema.validate`
- For route workflows, use `http.request` only if the runtime contract actually supports it.
- Do not keep Coze plugin names as runtime dependencies unless they are wrapped by a MyPrivateAgent provider or MCP capability.

### Missing Capability Rule

- Never ignore a missing capability just because the workflow can still be registered.
- If a manifest references an unsupported capability such as `http.request`, explicitly surface the gap.
- First try to resolve the gap by:
  - mapping it to an existing supported capability or shared service, or
  - adding the executor or contract support when that is the intended project direction.
- If the gap cannot be closed yet, keep the workflow blocked or draft and explain why in the acceptance notes.
- Do not silently downgrade, skip, or hand-wave missing dependencies in docs, tests, or execution results.

## 6. Migrate Prompts

- Move Coze prompt content into:
  - `prompts/system.md`
  - `prompts/task.md`
- Keep the prompt files maintainable.
- Keep the original export only as audit evidence.

## 7. Prepare Acceptance Fixtures

- Add at least one fixture and expected result.
- Keep the expected result compact and deterministic enough for review.
- If a live model is required, mark `acceptance.smoke.live_model_required = true`.

### Spreadsheet Workflow Acceptance

- Row count
- Field normalization
- Category mapping
- Blocked dependency handling

### Route Workflow Acceptance

- Single-match routing
- Collection/square-page routing
- Multi-match clarification
- No-match clarification

## 8. Run The Checks

Run checks in this order:

1. Confirm `workflow.yaml` exists and parses.
2. Confirm prompt files exist and are referenced by the manifest.
3. Confirm every `acceptance.examples[*].expected_path` file exists.
4. Run the registry read-only contract check.
5. Confirm the workflow shows the expected readiness state.
6. If the workflow is `review`, expect invoke to fail closed.
7. If the workflow is `active`, run a real fixture-based invoke.
8. Compare the returned JSON to the expected example.
9. Record the smoke result, blocker reason, and promotion decision.

### Workflow Lab Replay

- Use `/workflow-lab` to inspect the registry list, detail view, dependency mapping, and acceptance examples.
- Replay each acceptance example from the lab instead of relying on ad hoc shell commands.
- Confirm the lab replay result shows the returned JSON, expected diff, run id, status, and trace summary.
- If the lab replay is blocked, record the blocker and keep the workflow in `draft` or `review`.

## 9. Handle Route Workflows Carefully

- Typical input: `user_input` plus optional `data[]` candidate list.
- Typical output: `command`, `params`, and `message`.
- Keep the scenario matrix aligned with the actual business behavior.
- If the route workflow uses HTTP steps in the original Coze export, keep that intent in `source.migration_notes`.
- Make sure the runtime capability list matches the actual executor support before promotion.

## 10. Publish The Evidence

- Add a `docs/integration/<workflow>-launch-acceptance` record.
- Record the exact input payloads and returned outputs.
- Record the runtime boundary: what was performed and what was not performed.
- Document blockers explicitly if any capability is still missing.

## 11. Collaboration Rules

- Each workflow has a primary owner and reviewers.
- Owners should edit only their workflow directory unless a shared runtime contract change is agreed.
- Cross-workflow direct imports are not allowed.
- Shared behavior must move into capability runtime, ToolRuntime, MCP Runtime, Skill Runtime, or a documented shared service.
- Production rollout requires registry readiness, acceptance evidence, and governance trace support.

## 12. Re-Run Template

Use this when you need to prove the workflow really executed:

1. Run focused tests in the project conda env, not `base`.
2. Capture the exact input payload used for the workflow invocation.
3. Capture the exact returned JSON, including `command`, `params`, `message`, `run_id`, `status`, and trace metadata when present.
4. Compare the returned values against the acceptance example matrix.
5. If a dependency or capability is missing, name it explicitly, show the blocker, and explain the attempted fix.
6. For route workflows, verify all four scenario types before treating the workflow as a reusable sample.
7. Prefer Workflow Lab replay output as the canonical handoff artifact for other contributors.

## 13. When Something Is Missing

- Say it clearly.
- Identify the missing capability or file.
- Explain what you tried.
- Explain what remains blocked.
- Do not skip the problem and pretend the workflow is fine.

## 14. References

- [REFERENCE.md](REFERENCE.md)
- [EXAMPLES.md](EXAMPLES.md)
