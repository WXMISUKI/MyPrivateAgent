## Why

The grounded-answer trial surface now tells callers whether a domain agent can enter a repo-side grounded-answer trial, but it still does not provide the stable package that a later answer path would consume. Without that package layer, callers must reconstruct citations, evidence posture, prompt bindings, and fallback semantics themselves.

This phase adds a deterministic dry-run package builder. It prepares a grounded-answer input package without invoking models, providers, or default chat behavior.

## What Changes

- Add the canonical `domain-agent-grounded-answer-package-dry-run` capability.
- Add a read-only package service that:
  - consumes grounded-answer trial reports or the same caller-supplied evidence inputs
  - emits a compact `grounded_answer_package`
  - preserves citations, prompt bindings, memory boundaries, fallback policy, blockers, and warnings
- Extend the domain-agent trial router with an explicit package dry-run endpoint.
- Keep provider invocation, model invocation, answer generation, memory writes, source binding creation, audit writes, and GraphRAG execution out of scope.

## Capabilities

### New Capabilities

- `domain-agent-grounded-answer-package-dry-run`: deterministic dry-run package builder for a future grounded-answer path.

### Modified Capabilities

- `domain-agent-grounded-answer-trial-surface`: clarify that trial reports may feed a package dry-run but still do not generate answers.
- `domain-agent-grounded-answer-promotion-gate`: clarify that promotion `go` is a prerequisite for a ready package, not an answer-generation permit.

## Impact

- Backend: adds one narrow package service and one additional domain-agent endpoint.
- Tests: adds focused service and router tests for ready, review, blocked, citation, and graph boundaries.
- Docs/specs: clarifies the layer between trial readiness and future answer composition.
- Runtime behavior: default `/api/chat` remains unchanged and no model/provider call is introduced.
