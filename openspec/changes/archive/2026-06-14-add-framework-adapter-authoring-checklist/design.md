## Context

The project already has Framework Adapter SPI modules, a registry, precheck, runtime pilot execution, external pilot, diagnostics, and Query Control mapping. These pieces are useful but not yet packaged as a stable authoring checklist for future adapters.

The new contract should sit above the existing runtime service as a read-only review surface. It should help adapter authors and reviewers answer: what must this adapter declare, what can it do now, what blocks promotion, and what remains explicitly out of scope.

## Goals / Non-Goals

**Goals:**

- Expose a compact checklist for a requested adapter id.
- Include required sections: identity, lifecycle mapping, readiness/precheck, governance/timeline, promotion gate, and non-goals.
- Return a conservative promotion review status using existing precheck evidence.
- Keep default chat entry disabled unless a future explicit change promotes it.

**Non-Goals:**

- No new framework runtime dependency.
- No new adapter implementation.
- No main chat routing change.
- No actual execution, external pilot call, or trace/audit write.
- No frontend redesign.

## Decisions

1. Implement as a side-effect-free runtime service method.

   Rationale: `FrameworkAdapterRuntimeService` already owns adapter registry and precheck behavior. A read-only method keeps the contract near the adapter boundary without adding a new route in this slice.

2. Use precheck evidence only when explicitly requested through existing safe code paths.

   Rationale: the checklist should not execute the adapter. It may call `adapter.health_check()` through `precheck_adapter(...)`, which is already defined as non-executing readiness evidence.

3. Default promotion review remains blocked for main chat.

   Rationale: a ready adapter precheck is not enough to enter default chat execution. Main chat promotion requires a future explicit OpenSpec change.

## Risks / Trade-offs

- Checklist may duplicate some runtime contract fields -> keep it compact and reference existing precheck concepts instead of copying full health payloads.
- Consumers may confuse adapter precheck ready with production promotion -> include `default_chat_entry = disabled` and `will_execute = false`.
- No endpoint in this slice means UI cannot fetch it directly yet -> acceptable because this phase is backend contract/read-model convergence.
