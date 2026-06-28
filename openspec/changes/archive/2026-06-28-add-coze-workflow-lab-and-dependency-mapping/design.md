## Context

MyPrivateAgent already has the foundation for migrated Coze workflows:

- `backend/coze_workflows/<workflow_id>/workflow.yaml` provides the asset registry source.
- `GET /api/coze-workflows` exposes workflow registry state.
- `POST /api/coze-workflows/{workflow_id}/invoke` and `POST /api/capabilities/{capability_id}/invoke` provide explicit invocation.
- `capability_runtime`, `service-providers`, and `provider-onboarding` already define the provider and capability management boundary.

The current gap is productization. Teams can register and invoke workflows, but they do not yet have a dedicated workflow diagnostic surface that shows inputs, examples, dependency mapping, provider readiness, expected-output comparison, and launch evidence. This makes multi-person Coze migration depend too much on hand-written commands and tribal knowledge.

## Goals / Non-Goals

**Goals:**

- Add a Coze Workflow Lab contract for workflow list/detail, examples, invoke, expected-output comparison, dependency mapping, and trace summary.
- Keep migrated workflow invocation on the existing capability runtime path.
- Make unsupported Coze nodes and missing runtime capabilities visible as machine-readable blockers.
- Define how workflows that need files, OCR, VLM, RAG, HTTP, spreadsheet parsing, or other providers map to existing capability/provider contracts.
- Preserve a clear handoff between workflow migration and future model provider registry work.

**Non-Goals:**

- Build a visual workflow designer.
- Build a full model provider registry in this change.
- Enable default `/api/chat` routing to migrated workflows.
- Add hidden provider clients inside workflow directories.
- Replace existing provider management, capability runtime, or onboarding contracts.

## Decisions

1. Workflow Lab consumes backend contracts instead of deriving behavior in the frontend.

   Rationale: workflow readiness, schema, dependency mapping, and provider status must remain backend-owned so command-line tests, API clients, and the future UI see the same truth.

   Alternative considered: frontend reads `workflow.yaml` directly. Rejected because it bypasses registry validation and would duplicate dependency logic.

2. Dependency mapping is a first-class read model.

   Rationale: Coze exports contain platform-specific nodes such as HTTP plugins, OCR plugins, link readers, RAG connectors, and model nodes. Each must map to a MyPrivateAgent capability, provider, artifact flow, or explicit blocker.

   Alternative considered: keep dependency notes as prose in README files. Rejected because migration blockers must be testable and machine-readable.

3. Invocation stays on capability runtime.

   Rationale: `coze.workflow.<workflow_id>` already gives workflows a stable capability id. External callers should use the same envelope, trace, and fail-closed behavior as other capabilities.

   Alternative considered: create a separate external workflow API. Rejected because it creates a parallel execution path and fragments governance.

4. File-heavy workflows use artifact references and provider-owned jobs.

   Rationale: OCR, VLM, large document parsing, video, and batch workflows may exceed synchronous API limits. Workflow Lab can help test them, but the runtime should not hide large files as local paths.

   Alternative considered: synchronous upload and local processing for everything. Rejected because it would not scale and would blur provider ownership.

5. Model provider registry is a follow-up change.

   Rationale: model list, base URL, API key, context length, modality tags, default/fallback model policy, and model health are broader than Coze migration. This change should link to that future contract but not implement it.

## Risks / Trade-offs

- [Risk] Workflow Lab becomes a second execution path. -> Mitigation: Lab must call the same invoke endpoints used by API callers.
- [Risk] Teams mark workflows active before provider readiness is real. -> Mitigation: dependency mapping and launch evidence must show provider readiness and blockers.
- [Risk] File workflows rely on local filesystem paths. -> Mitigation: specs require artifact/file references for reusable lab and external invocation.
- [Risk] Model configuration work is underestimated. -> Mitigation: explicitly defer full model provider registry to a follow-up OpenSpec while preserving dependency hooks.
- [Risk] Frontend form rendering becomes too broad. -> Mitigation: start with JSON schema-driven forms, examples, file inputs, and raw JSON override instead of a visual workflow designer.

## Migration Plan

1. Add backend read contracts for workflow detail, examples, dependency mapping, and invocation preview.
2. Add focused tests for dependency mapping, example loading, expected-output comparison, and blocked capability behavior.
3. Add docs for workflow API exposure, provider mapping, and Workflow Lab usage.
4. Add frontend Workflow Lab after backend contracts are stable.
5. Use existing migrated workflows as fixtures: `hazardous_project_list_recognition` and `szzg_agent_encapsulation_route`.

## Open Questions

- Should external caller authentication be handled by an existing API auth layer or a new workflow API key policy?
- Should workflow example invocation produce persistent trace records immediately, or only compact evidence until the trace writer is wired?
- Should artifact upload be implemented inside Workflow Lab first, or should it wait for a unified artifact service contract?
- Which follow-up change owns full model provider registry: model provider registry, PromptOps, or provider onboarding?
