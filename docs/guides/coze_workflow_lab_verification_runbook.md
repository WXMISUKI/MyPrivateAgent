# Coze Workflow Lab Verification Runbook

This runbook shows how to verify migrated Coze workflows in MyPrivateAgent using the backend registry, the workflow lab, and the frontend UI.

## Scope

Use this runbook when you need to confirm that a migrated workflow:

- is exposed through `coze.workflow.<workflow_id>`
- has correct dependency mapping
- can replay acceptance examples through the same capability/runtime envelope used in production
- stays fail-closed for draft, review, invalid, blocked, deprecated, or archived workflows

This runbook does not cover model provider registry setup. That remains a separate follow-up change.

## Prerequisites

- Project conda environment is available as `myenv`
- Backend dependencies are installed
- Frontend dependencies are installed
- The workflow already exists under `backend/coze_workflows/<workflow_id>/`

## Step 1: Run Backend Contract Tests

Run the focused backend suite in `myenv`:

```powershell
conda run -n myenv --no-capture-output python -m pytest backend/tests/coze_workflow_lab_test.py backend/tests/coze_workflow_registry_test.py -q
```

Expected result:

- `dependency_mapping` is present and readable
- `route` workflow dependency mapping shows `http.request`
- file workflows expose artifact input metadata
- example replay succeeds for active workflows
- blocked workflows fail closed

## Step 2: Run Frontend Contract Tests

Run the Workflow Lab UI tests from `frontend-vue`:

```powershell
cmd /c npm test -- --run src/views/__tests__/WorkflowLabView.test.js src/components/__tests__/AppSidebar.test.js
```

Expected result:

- the sidebar exposes a dedicated `Workflow Lab` entry
- the lab page loads registry data
- the lab detail view renders dependency mapping and examples
- the replay action returns `run_id`, `status`, and expected comparison output

## Step 3: Validate OpenSpec State

Verify the change is still valid:

```powershell
openspec validate add-coze-workflow-lab-and-dependency-mapping --strict
```

Expected result:

- change validates successfully

## Step 4: Inspect Workflow Registry

Fetch the workflow list:

```http
GET /api/coze-workflows
```

Check for:

- `workflow_id`
- `name`
- `status`
- `capability_id`
- `readiness.status`
- `launch_evidence.status`
- dependency mapping categories
- blocker reasons when a node is not supported

## Step 5: Inspect Workflow Detail

Fetch the workflow detail:

```http
GET /api/coze-workflows/{workflow_id}
```

Confirm the response includes:

- input schema
- output schema
- prompts metadata
- acceptance examples
- governance
- asset paths
- dependency mapping
- invoke contract metadata for promoted workflows

## Step 6: Replay an Example

Replay one acceptance example:

```http
POST /api/coze-workflow-lab/{workflow_id}/examples/{example_id}/invoke
```

Expected result:

- `status = completed` for active and ready workflows
- `run_id` is present
- `trace_summary` is present
- `expected_comparison.status = match` when the fixture matches
- dependency mapping should already classify each node as `runtime_capability`, `provider_backed`, `artifact_input`, or `explicit_blocker`

If the workflow is not ready, expect:

- `status = blocked`
- `error.code = COZE_WORKFLOW_LAB_REPLAY_BLOCKED`
- the blocker list explains why the replay was refused

## Step 7: Check Production Invocation

Call the production capability envelope:

```http
POST /api/coze-workflows/{workflow_id}/invoke
```

Confirm that the response includes:

- `workflow_id`
- `capability_id`
- `workflow_version`
- `run_id`
- `status`
- `authorization`
- `invocation_policy`
- `trace_summary`

If you need to validate the shared capability path, call:

```http
POST /api/capabilities/{capability_id}/invoke
```

That endpoint should preserve the same production envelope.

## Step 8: Verify Frontend UI

Open the `Workflow Lab` entry from the sidebar.

Check that the page shows:

- workflow list
- status and readiness
- owner and capability id
- launch evidence
- detail view
- dependency mapping
- replay result

## Step 9: Verify File Workflows

For spreadsheet or file-based workflows, make sure the replay uses runtime-managed references instead of raw local paths.

Valid reference styles:

- `content_ref`
- `artifact_id`
- `runtime_file_ref`

## Step 10: Verify Dependency Mapping

Use these rules when judging the mapping:

- `ready` means the capability is mapped and the runtime contract can serve it
- `blocked` means a capability, provider, or node is still missing
- `declared` means the item is explicit but not yet promoted to a ready runtime mapping
- `artifact_input` means file or upload input is represented as a runtime reference

## Minimal Acceptance Checklist

- backend tests pass
- frontend tests pass
- OpenSpec validation passes
- workflow list is visible
- workflow detail is visible
- at least one example replay succeeds for active workflows
- blocked workflows remain fail-closed

## Troubleshooting

- If `http.request` is missing, the workflow should remain blocked or mapped to a deterministic local route rule.
- If file input uses a local path, convert it to a runtime-managed reference.
- If a provider-backed capability is not configured, check the onboarding and service-provider read models first.
- If the replay result differs from expected JSON, keep the workflow in review until the fixture or implementation is corrected.

## Related Docs

- [`docs/guides/coze_migration_workflow_authoring.md`](/D:/AI/AIcode/MyPrivateAgent/docs/guides/coze_migration_workflow_authoring.md)
- [`docs/guides/capability_runtime_registry.md`](/D:/AI/AIcode/MyPrivateAgent/docs/guides/capability_runtime_registry.md)
- [`docs/architecture/runtime_contracts.md`](/D:/AI/AIcode/MyPrivateAgent/docs/architecture/runtime_contracts.md)
