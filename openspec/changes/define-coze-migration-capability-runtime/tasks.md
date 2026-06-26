## 1. Authoring Contract And Templates

- [x] 1.1 Create `backend/coze_workflows/README.md` with workflow directory rules, ownership rules, naming rules, and direct-import prohibition.
- [x] 1.2 Add a reusable `workflow.yaml` template documenting required sections for identity, source, entrypoint, inputs, outputs, prompts, dependencies, governance, acceptance, and status.
- [x] 1.3 Add one non-production sample workflow directory that demonstrates prompt references and acceptance examples without changing default chat behavior.
- [x] 1.4 Verify the sample manifest can be read as plain YAML and that required referenced files exist.

## 2. Side-Effect-Free Registry

- [x] 2.1 Implement a Coze migration workflow registry service that scans `backend/coze_workflows/*/workflow.yaml`.
- [x] 2.2 Normalize valid manifests into compact workflow contracts with `workflow_id`, `version`, `owner`, `status`, dependencies, governance, acceptance, asset paths, and readiness.
- [x] 2.3 Mark invalid manifests as `invalid` with machine-readable missing field errors while keeping unrelated workflows discoverable.
- [x] 2.4 Add focused backend tests for valid manifest, missing required field, missing prompt file, missing acceptance example, and empty registry.
- [x] 2.5 Verify registry inspection does not execute workflows, call models, invoke tools, create runs, or mutate runtime state.

## 3. Runtime Surface And Domain Agent Linkage

- [x] 3.1 Expose the Coze workflow registry as a read-only contract through Runtime Surface or a dedicated read endpoint.
- [x] 3.2 Extend domain agent manifest normalization to preserve `capabilities.coze_workflows` references.
- [x] 3.3 Surface missing Coze workflow references as warnings or blockers without blocking unrelated domain agents.
- [x] 3.4 Add focused backend tests for domain agent Coze workflow references and missing reference behavior.

## 4. Unified Capability Runtime Integration

- [x] 4.1 Map active and ready Coze workflows to optional capability ids such as `coze.workflow.<workflow_id>`.
- [x] 4.2 Ensure draft/review workflows remain visible in the Coze registry but are not exposed as default callable production capabilities.
- [x] 4.3 Add capability runtime tests for ready workflow listing and draft workflow exclusion.
- [x] 4.4 Keep the first implementation side-effect-free until an explicit invoke task is started.

## 5. Unified Invocation Slice

- [x] 5.1 Add the minimal unified invocation path for ready Coze workflows using the standard capability/runtime response envelope.
- [x] 5.2 Validate invocation payloads against workflow input schema before execution.
- [x] 5.3 Return stable structured errors for unknown workflow, invalid manifest, blocked status, missing dependency, and schema validation failure.
- [x] 5.4 Attach invocation metadata to Runtime Core trace using `workflow_id`, `workflow_version`, `owner`, and `source = coze_migration`.
- [x] 5.5 Add focused tests for successful deterministic sample invocation and blocked dependency invocation.

## 6. Governance, Documentation, And Validation

- [x] 6.1 Update `docs/architecture/runtime_contracts.md` with Coze migration workflow registry, capability exposure, and invocation boundaries.
- [x] 6.2 Update `docs/roadmap/next_phase_hardening.md` with the Coze migration collaboration track and stop conditions.
- [x] 6.3 Add a developer guide for migrating Coze workflows, including directory layout, manifest fields, Prompt migration, dependency declaration, owner responsibilities, and acceptance examples.
- [x] 6.4 Run `openspec.cmd validate define-coze-migration-capability-runtime --strict` or the repository-supported equivalent.
- [x] 6.5 Run focused backend tests added by this change; do not run full build unless contract changes require it.
