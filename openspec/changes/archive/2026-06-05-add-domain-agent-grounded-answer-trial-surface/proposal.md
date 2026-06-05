## Why

The grounded answer promotion gate can now decide whether a domain agent is ready for a repo-side grounded-answer trial, but callers still lack a stable way to request and inspect that trial decision. Without a small trial surface, integration remains tied to direct service imports or ad hoc evidence handoff.

This phase adds an explicit opt-in trial surface that packages grounding and promotion decisions into a caller-readable report while preserving the current default chat behavior.

## What Changes

- Add the canonical `domain-agent-grounded-answer-trial-surface` capability.
- Add a minimal read-only trial service that:
  - accepts caller-supplied provider, PromptOps, MemoryOps, eval, and evidence pack data
  - evaluates grounding policy
  - evaluates the grounded answer promotion gate
  - returns a compact trial report
- Add a narrow API endpoint for explicit trial requests.
- Keep `/api/chat` retrieval injection disabled.
- Keep answer composition, provider invocation, source binding creation, memory writes, audit writes, and GraphRAG execution out of scope.

## Capabilities

### New Capabilities

- `domain-agent-grounded-answer-trial-surface`: explicit opt-in trial report surface for domain-agent grounded answer readiness.

### Modified Capabilities

- `domain-agent-grounded-answer-promotion-gate`: clarify that the trial surface consumes promotion decisions but does not promote runtime behavior.
- `agent-grounding-policy`: clarify that the trial surface may evaluate grounding decisions from caller-supplied evidence packs.

## Impact

- Backend: adds one small service and one narrow router.
- Tests: adds focused service and router tests for go, review, blocked, citation, and GraphRAG boundaries.
- Docs/specs: documents the trial surface as a caller integration entry, not a default chat behavior change.
- Runtime behavior: default chat remains unchanged and no provider is invoked by the trial surface.
