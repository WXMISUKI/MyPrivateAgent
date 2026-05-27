## Context

MyPrivateAgent already contains a substantial runtime control surface: Runtime Surface, ToolRuntimeService, Query Control Plane, Runtime Contract Gate, Governance Timeline, channel promotion gates, recovery governance, and child executor guardrails. Recent market review shows that mature agent frameworks are now plentiful, but they mainly solve execution and workflow construction. They do not remove the need for local enterprise governance, audit, adapter normalization, business-system integration, and long-lived runtime contracts.

The current documentation partially says the project is not bound to one external framework, but the stronger positioning is not yet formalized as a spec-level rule. This change makes that positioning explicit before future framework adapter work resumes.

## Goals / Non-Goals

**Goals:**

- Make "Agent Runtime Control Plane" the official project positioning.
- Define external frameworks as adapter-backed execution engines under local contracts.
- Clarify that Runtime Core, Tool Runtime, Query Control, Governance, and OpenSpec remain local truth sources.
- Align roadmap, architecture docs, OpenSpec context, and reference mapping.
- Produce a planning sequence for upcoming work: spec first, implementation second, archive third, git submission last.

**Non-Goals:**

- No runtime migration to a single external framework.
- No new adapter implementation in this change.
- No contract payload change in backend APIs.
- No UI behavior change.
- No default main-chat execution through external adapters.

## Decisions

### Decision 1: Position MyPrivateAgent Above Agent Frameworks

MyPrivateAgent will be documented as the enterprise control plane that can host multiple framework adapters.

Alternative considered: choose one mature framework as the project foundation. This would reduce short-term integration work, but it would also bind governance, permissions, read models, and audit semantics to one vendor/community lifecycle.

### Decision 2: Treat Frameworks As Execution Adapters

LangGraph, OpenAI Agents SDK, Qwen-Agent, CrewAI, DeerFlow, Agno, and future frameworks can be evaluated as execution adapters. Each adapter must map its lifecycle into local Query Control and Governance contracts before it can be promoted.

Alternative considered: expose framework-native payloads directly to the frontend. That would make the first adapter faster but would fracture Runtime Surface and Governance Timeline semantics.

### Decision 3: Keep Local Runtime Contracts As The Stable Boundary

`RuntimeSurfaceService`, `ToolRuntimeService`, `QueryControlPlane`, `RuntimeContractGate`, and Governance Timeline contracts remain the primary integration boundary. External frameworks can influence implementation strategy but must not redefine these contracts directly.

Alternative considered: let each adapter define its own governance model. That would increase adapter autonomy but would make cross-framework observability, policy, and audit inconsistent.

### Decision 4: Plan Future Work In Gates

Future framework work should move through:

1. Specification: define adapter boundary, lifecycle mapping, promotion readiness, and non-goals.
2. Implementation: add one focused adapter or contract slice.
3. Archive: sync canonical specs and roadmap after tasks pass.
4. Git submission: commit only after verification and archive state are clear.

Alternative considered: implement adapters opportunistically. The existing archived changes show this project benefits from explicit spec gates, especially around runtime and governance semantics.

## Risks / Trade-offs

- Risk: The positioning could become too abstract and slow down feature delivery. -> Mitigation: Require every future adapter change to name a concrete minimal slice and verification command.
- Risk: External framework capabilities may tempt direct integration that bypasses local contracts. -> Mitigation: Canonical specs must require adapter lifecycle mapping and promotion gates.
- Risk: Documentation-only changes can drift from code. -> Mitigation: Keep this change limited to positioning, then open implementation changes only when a concrete adapter or gate is ready.
- Risk: Maintaining multiple adapter options increases planning overhead. -> Mitigation: Prefer one production-facing adapter pilot at a time, with explicit non-goals.

## Migration Plan

This is a documentation/spec migration:

1. Add canonical positioning spec.
2. Update existing runtime harness reference spec.
3. Update architecture and roadmap truth sources.
4. Validate OpenSpec status.
5. Archive the change after task completion.

Rollback is straightforward: revert the documentation/spec changes. No database, runtime contract, or frontend migration is involved.

## Open Questions

- Which external adapter should be the next concrete implementation candidate: OpenAI Agents SDK, Qwen-Agent, LangGraph, DeerFlow, or CrewAI?
- Should adapter authoring checklist become its own canonical spec after this positioning change?
- Should framework adapter promotion reuse the existing channel promotion gate or receive a narrower adapter-specific gate?
