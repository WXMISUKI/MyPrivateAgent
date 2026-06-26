# Coze Workflow Migration Reference

## Recommended Scope

- Asset root: `backend/coze_workflows/<workflow_id>/`
- Registry root: `backend/coze_workflows/*/workflow.yaml`
- Capability id pattern: `coze.workflow.<workflow_id>`

## Implementation Stages

### Stage 1: Authoring

- Create or update `workflow.yaml`.
- Add prompt files under `prompts/`.
- Add acceptance fixtures under `examples/`.
- Preserve original Coze export material under `source/coze_export/` when available.

### Stage 2: Registry

- Confirm the registry scans manifests without importing workflow code.
- Confirm missing assets produce machine-readable blockers.
- Confirm invalid manifests remain visible but not callable.

### Stage 3: Runtime Surface

- Expose registry output through a read-only contract.
- Preserve `capabilities.coze_workflows` references in domain agent manifests.
- Keep unrelated agents discoverable when a referenced workflow is missing.

### Stage 4: Capability Runtime

- Expose only ready workflows as callable capabilities.
- Keep draft and review workflows visible in the migration registry.
- Keep readiness and invoke errors stable and machine-readable.

### Stage 5: Invoke

- Validate request payloads against the workflow input schema.
- Return `run_id`, `status`, `result`, `error`, and trace references.
- Reject unknown workflows, blocked workflows, and invalid manifests with fail-closed errors.

## Test Matrix

- Happy path manifest normalization
- Missing required manifest field
- Missing prompt file
- Missing acceptance example
- Empty registry
- Domain agent references existing workflow
- Domain agent references missing workflow
- Ready workflow listed as capability
- Draft workflow excluded from production callable listing
- Successful deterministic invocation
- Blocked invocation on missing dependency

## Launch Acceptance

- Registry is read-only.
- Workflow assets are organized under a single owner.
- Capability id is stable and documented.
- Related docs and OpenSpec tasks are updated.
- Test evidence is captured before promoting to active usage.

