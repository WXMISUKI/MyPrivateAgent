## Why

The grounded-answer stack now reaches a deterministic package dry-run, but callers still cannot run a final, explicit composition trial over that package. Without a composition trial, the stack stops one layer before the actual answer path shape and leaves the final controlled answer preview undefined.

This phase adds a minimal grounded-answer composition trial that consumes a ready package and returns a controlled answer preview without changing default chat behavior.

## What Changes

- Add the canonical `domain-agent-grounded-answer-composition-trial` capability.
- Add a read-only composition trial service that:
  - consumes a grounded-answer package dry-run or the same raw evidence inputs
  - returns a bounded answer preview with used citations and fallback semantics
  - blocks or reviews when package readiness is insufficient
- Extend the domain-agent router with an explicit composition trial endpoint.
- Keep provider invocation, default `/api/chat` retrieval injection, source binding, memory writes, audit writes, and GraphRAG execution out of scope.

## Capabilities

### New Capabilities

- `domain-agent-grounded-answer-composition-trial`: explicit opt-in grounded answer composition preview over a ready package.

### Modified Capabilities

- `domain-agent-grounded-answer-package-dry-run`: clarify that a ready package may feed composition trial, but not default answer generation.
- `domain-agent-grounded-answer-trial-surface`: clarify that composition trial is downstream of trial/package and remains opt-in.

## Impact

- Backend: adds one narrow composition trial service and one route extension.
- Tests: adds focused service/router tests for ready, review, blocked, citation, and graph boundaries.
- Docs/specs: records the final phase of this grounded-answer control-plane line.
- Runtime behavior: default `/api/chat` remains unchanged.
