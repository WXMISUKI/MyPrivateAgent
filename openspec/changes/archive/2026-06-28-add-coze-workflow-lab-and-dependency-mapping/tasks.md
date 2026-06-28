## 1. Backend Workflow Lab Read Contracts

- [x] 1.1 Add a workflow lab read service that assembles list/detail contracts from the existing Coze workflow registry without executing workflows.
- [x] 1.2 Add workflow detail output with input schema, output schema, prompts metadata, acceptance examples, governance, capability id, readiness, and launch evidence path.
- [x] 1.3 Add example loading support that reads declared acceptance fixtures and expected JSON without mutating workflow state.
- [x] 1.4 Add focused backend tests for workflow lab list/detail/example loading using `hazardous_project_list_recognition` and `szzg_agent_encapsulation_route`.

## 2. Dependency Mapping

- [x] 2.1 Implement dependency mapping for manifest `dependencies.runtime_capabilities`, providers, tools, MCP capabilities, skills, and unsupported nodes.
- [x] 2.2 Map known Coze workflow node types to MyPrivateAgent capability ids or explicit unsupported blockers.
- [x] 2.3 Link provider-backed dependencies to `service-providers` and `provider-onboarding` readiness fields when available.
- [x] 2.4 Add file/artifact dependency metadata for file upload, spreadsheet, OCR, VLM, RAG, and provider-owned job workflows.
- [x] 2.5 Add focused backend tests for supported dependency, unsupported dependency, provider-backed dependency, and file/artifact dependency mapping.

## 3. Invocation Preview And Expected Diff

- [x] 3.1 Add workflow lab example invocation that delegates to the same workflow/capability invocation path used by production callers.
- [x] 3.2 Add expected-output comparison with `match`, `mismatch`, and compact diff summary states.
- [x] 3.3 Preserve blocked behavior for draft, review, invalid, blocked, deprecated, and archived workflows.
- [x] 3.4 Add focused tests for successful example replay, mismatch diff, and blocked replay.

## 4. External Workflow Invocation Contract

- [x] 4.1 Confirm `coze.workflow.<workflow_id>` capabilities expose input/output schema, workflow status, readiness, owner, version, and asset paths.
- [x] 4.2 Ensure external invocation responses include workflow id, capability id, run id, status, workflow version, result or error, and trace summary.
- [x] 4.3 Add authorization/policy placeholder fields or explicit blockers for external callers without implementing a new auth system.
- [x] 4.4 Add tests for active workflow invocation, not-ready workflow invocation, and version metadata.

## 5. Frontend Workflow Lab

- [x] 5.1 Add a workflow lab page or panel that lists registered Coze workflows with status, readiness, owner, capability id, and launch evidence status.
- [x] 5.2 Add workflow detail view with schema-driven input hints, examples, dependency mapping, provider readiness links, and governance notes.
- [x] 5.3 Add example replay action that shows returned JSON, expected diff, run id, status, blockers, and trace summary.
- [x] 5.4 Keep Workflow Lab separate from default chat and provider settings; it must not change default chat behavior.
- [x] 5.5 Add focused frontend tests or documented manual verification for list/detail/replay flows.

## 6. Documentation And Migration Guides

- [x] 6.1 Update `docs/guides/coze_migration_workflow_authoring.md` with Workflow Lab usage and dependency mapping examples.
- [x] 6.2 Update `.trae/skills/coze-workflow-migration/` with lab replay and dependency mapping checklist steps.
- [x] 6.3 Update `docs/guides/capability_runtime_registry.md` with migrated workflow capability invocation guidance.
- [x] 6.4 Update `docs/architecture/runtime_contracts.md` and `docs/roadmap/next_phase_hardening.md` with the new lab and dependency mapping boundary.
- [x] 6.5 Add or update `docs/integration/*-launch-acceptance` examples to show replayable evidence.

## 7. Validation And Follow-up Boundaries

- [x] 7.1 Run focused backend tests for Coze workflow registry, lab contracts, dependency mapping, and capability invocation.
- [x] 7.2 Run focused frontend tests if the Workflow Lab UI is implemented in this change.
- [x] 7.3 Run `openspec validate add-coze-workflow-lab-and-dependency-mapping --strict`.
- [x] 7.4 Document model provider registry as a separate follow-up change for model list, base URL, API key, modality tags, fallback policy, and health checks.
- [ ] 7.5 Archive the change only after tests pass and docs reflect the implemented scope.
