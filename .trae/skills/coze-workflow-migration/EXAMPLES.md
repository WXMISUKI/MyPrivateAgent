# Coze Workflow Migration Examples

## Example 1: New Workflow Landing

1. Create `backend/coze_workflows/customer_intake/`.
2. Add `workflow.yaml`, `prompts/system.md`, `prompts/task.md`, and `examples/*.json`.
3. Keep `status: draft` until registry checks pass.
4. Update owner, dependency, and acceptance fields.

## Example 2: Migration Review

1. Confirm the manifest is discoverable by the registry.
2. Confirm prompt references point to existing files.
3. Confirm acceptance examples exist and are deterministic.
4. Confirm domain agent references use `capabilities.coze_workflows`.

## Example 3: Launch Readiness

1. Registry status is `ready` or `degraded` with understood blockers.
2. Capability exposure is aligned with workflow status.
3. Invoke flow is documented and tested.
4. Acceptance evidence is linked in docs or task notes.

