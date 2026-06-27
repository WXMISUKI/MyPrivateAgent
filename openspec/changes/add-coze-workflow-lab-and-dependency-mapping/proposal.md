## Why

Coze workflow migration has moved beyond asset registration: migrated workflows now need stable API invocation, dependency mapping, provider readiness, and a local test surface that lets teams replay examples without hand-written scripts.

This change closes the gap between "workflow is registered" and "workflow is safely testable, callable, and diagnosable by multiple teams."

## What Changes

- Add a Coze Workflow Lab contract for listing migrated workflows, reading workflow details, loading examples, invoking examples, comparing expected output, and showing trace/readiness evidence.
- Add dependency mapping for migrated Coze nodes and manifest dependencies, including unsupported capability blockers and provider readiness links.
- Harden the external invocation contract for workflows that are exposed through `coze.workflow.<workflow_id>` capability ids.
- Define file/artifact handling expectations for workflows that require upload, OCR, VLM, spreadsheet parsing, RAG, or external providers.
- Define the handoff boundary between Coze workflow migration and model/provider configuration.
- Add launch acceptance requirements so each migrated workflow can publish replayable `docs/integration/*-launch-acceptance` evidence.

Non-goals:

- Do not build a general visual workflow designer in this change.
- Do not replace `capability_runtime`, `service-providers`, or `provider-onboarding` with a parallel execution system.
- Do not implement a full model provider registry in this change; model registry should be proposed as a follow-up change.
- Do not enable default `/api/chat` routing to migrated workflows.
- Do not add hidden local dependencies for OCR, VLM, RAG, or model providers inside workflow directories.

## Capabilities

### New Capabilities

- `coze-workflow-lab`: Workflow test and diagnostic surface for registry details, examples, invocation, expected-output comparison, and launch evidence.
- `coze-workflow-dependency-mapping`: Coze node and manifest dependency mapping to local capabilities, providers, unsupported blockers, and readiness evidence.
- `coze-workflow-external-invocation`: API exposure and governance requirements for external callers invoking migrated workflows through capability ids.

### Modified Capabilities

- `unified-capability-runtime`: Clarify that migrated workflow invocation delegates to existing capability runtime and does not create a second provider execution path.
- `provider-service-consumption-contract`: Clarify how workflow dependencies link to provider readiness and explicit provider capability invocation without promoting default chat behavior.

## Impact

Affected backend areas:

- `backend/services/coze_workflow_registry_service.py`
- `backend/routers/coze_workflows.py`
- `backend/capability_runtime/*`
- `backend/routers/capabilities.py`
- `backend/capability_runtime/provider_consumption_service.py`
- Future workflow-lab service/router if needed

Affected frontend areas:

- A future workflow lab page or panel that consumes workflow registry, detail, examples, invoke, diff, dependency mapping, and trace summary contracts.
- Existing settings/provider panels may be linked for provider readiness but should not become workflow execution surfaces.

Affected docs and governance:

- `docs/guides/coze_migration_workflow_authoring.md`
- `.trae/skills/coze-workflow-migration/`
- `docs/guides/capability_runtime_registry.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
- `docs/integration/*-launch-acceptance`

Key dependencies:

- Existing `capability_runtime` remains the execution contract.
- Existing `service-providers` and `provider-onboarding` remain the provider management/readiness contracts.
- Model provider registry is a related follow-up, not part of this change.
