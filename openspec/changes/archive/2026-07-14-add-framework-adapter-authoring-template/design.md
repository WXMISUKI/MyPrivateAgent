## Context

`framework-adapter-authoring-checklist` already exposes a side-effect-free review contract for registered adapters. It includes identity, lifecycle mapping, readiness checks, governance timeline requirements, promotion gate, non-goals, precheck summary, and boundary flags.

Runtime Plane Stage 1 then proved three local adapter envelopes:

- `simple_agent`: basic request/event/result shape.
- `tool_agent`: controlled read-only tool observation.
- `approval_agent`: high-risk tool intent becomes `approval_pending` without executing the handler.

The missing bridge is not another local runtime feature. The missing bridge is a reusable authoring template that turns those proofs into a repeatable adapter contract for mature runtimes such as LangGraph and AgentRun.

## Goals / Non-Goals

**Goals:**

- Add `authoring_template` to the existing checklist response.
- Make the template machine-readable and stable enough for reviewers, docs, and future scaffolding.
- Point adapter authors to expected files/modules, required contracts, runtime-plane proof mappings, governance projection expectations, smoke tests, and promotion gate requirements.
- Preserve the existing conservative promotion review semantics.

**Non-Goals:**

- No real LangGraph or AgentRun execution.
- No new framework dependency.
- No default main chat promotion.
- No trace/audit mutation from checklist generation.
- No worker, scheduler, checkpoint, sandbox, provider binding, or tool registry change.
- No new parallel adapter service.

## Decisions

1. Extend `FrameworkAdapterRuntimeService.build_adapter_authoring_checklist(...)` instead of adding a parallel service.

   Rationale: checklist generation is already the canonical adapter review entrypoint. Extending it keeps future framework adapter work behind one contract.

   Alternative considered: add a new `FrameworkAdapterTemplateService`. Rejected because it would split review, precheck, and authoring guidance into multiple read models.

2. Keep `contract_version` at `framework-adapter-authoring-checklist-v1`.

   Rationale: this is additive. Existing fields and semantics remain unchanged. Consumers that ignore `authoring_template` continue to work.

   Alternative considered: create v2. Rejected until a breaking shape change is needed.

3. Build the template from adapter identity plus static runtime-plane contract knowledge.

   Rationale: this template describes how to author an adapter. It must not depend on executing or importing an external framework.

   Alternative considered: introspect framework packages. Rejected because package presence belongs to precheck and would make checklist generation less predictable.

## Risks / Trade-offs

- [Risk] The template could be mistaken for production readiness. -> Mitigation: include `will_execute = false`, `default_chat_entry = disabled`, explicit non-goals, and boundary flags in both promotion review and template.
- [Risk] The template becomes too generic to guide real teams. -> Mitigation: include concrete expected files, required contracts, Stage 1 proof mappings, and minimum smoke tests.
- [Risk] It encourages local runtime expansion. -> Mitigation: docs state that next work should implement adapters to mature runtimes, not extend local graph/checkpoint/scheduler.

## Migration Plan

1. Add the OpenSpec delta.
2. Extend the backend checklist contract additively.
3. Update focused tests for ready, blocked, and unknown adapter cases.
4. Update roadmap/architecture docs and add a review note.
5. Validate OpenSpec and run the focused pytest module.
6. Archive the change after implementation.

Rollback: remove the additive `authoring_template` field and tests/docs references. Existing checklist behavior remains intact.

## Open Questions

- Whether a later slice should expose this template through a dedicated API route or frontend governance card. Not in scope for this change.
- Whether the first real external adapter should target LangGraph or AgentRun. This change keeps both as adapter targets and does not choose production infrastructure.
