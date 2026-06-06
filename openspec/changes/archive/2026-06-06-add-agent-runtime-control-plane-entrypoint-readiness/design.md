# Design

## Entry Point Shape

Add `docs/architecture/agent_runtime_control_plane_entrypoint.md` as the first architecture document for new maintainers. It should answer:

- What is MyPrivateAgent now?
- Which layer owns Runtime Core, Capability, Governance, Delivery, and Provider boundaries?
- What should a caller use today?
- What should a maintainer read next?
- What should not be promoted by default yet?

This document is intentionally short and index-like. It should point to deeper docs rather than copying them.

## Checklist Shape

Add `docs/guides/project_entrypoint_checklist.md` as a task-oriented checklist:

- Local verification checklist.
- Domain-agent trial checklist.
- External provider boundary checklist.
- Runtime/SDK extension checklist.
- Framework adapter checklist.
- Stop/do-not-do checklist.

The checklist is meant to prevent the next phase from drifting back into local evidence chains or accidental behavior promotion.

## Existing Docs To Update

- `README.md`: replace stale project positioning with the current Agent Runtime Control Plane posture and link to the entrypoint.
- `docs/architecture/current_architecture.md`: make the new entrypoint the first recommended reading item and keep current architecture as the factual detail page.
- `docs/roadmap/next_phase_hardening.md`: record that domain-agent repo-side trial readiness has reached a pause line and the next default work should return to runtime/control-plane entrypoint and SDK/runtime priorities.

## Boundary

This change is documentation and spec only. It must not edit backend runtime code, frontend behavior, or service contracts.

## Verification

Run:

```powershell
cmd /c openspec validate add-agent-runtime-control-plane-entrypoint-readiness --strict
cmd /c openspec validate --all --strict
```

No backend service start is required.
