# Coze Workflow Migration Examples

## Example 1: Spreadsheet Migration

1. Create `backend/coze_workflows/hazardous_project_list_recognition/`.
2. Add `workflow.yaml`, `prompts/system.md`, `prompts/task.md`, and `examples/*.json`.
3. Keep the workflow in `review` until registry checks and fixture validation pass.
4. Promote to `active` only after invoke and smoke evidence are complete.
5. Use Workflow Lab to replay `hazardous_project_list_sample` and record the returned JSON plus diff.

## Example 2: Route Migration

1. Create `backend/coze_workflows/szzg_agent_encapsulation_route/`.
2. Use `user_input` plus optional `data[]` candidates as the input contract.
3. Cover `route_agent`, `route_square`, `clarify_multi`, and `clarify_none` in acceptance.
4. Publish a `docs/integration/*-launch-acceptance` record with the exact input/output matrix.
5. Use Workflow Lab to inspect `http.request` dependency mapping before treating the workflow as reusable.

## Example 3: Missing Capability

1. A manifest references `http.request`.
2. The runtime does not support it yet.
3. Surface the blocker explicitly.
4. Either add the executor support or keep the workflow blocked and explain why.
