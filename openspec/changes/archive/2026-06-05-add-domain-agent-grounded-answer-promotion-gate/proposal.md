## Why

MyPrivateAgent has closed the provider-side access path, PromptOps visibility, MemoryOps boundaries, multi-turn eval gate, and agent grounding policy decision gate. The remaining gap is a small caller-owned readiness decision that tells whether a domain agent may enter a grounded-answer trial without changing default chat behavior.

This phase creates that minimal promotion gate. It aggregates existing control-plane evidence into `go`, `review`, or `blocked` so a caller can see whether the next action is a real repo-side trial, more review, or missing prerequisite work.

## What Changes

- Add a canonical `domain-agent-grounded-answer-promotion-gate` capability.
- Add a side-effect-free promotion service that aggregates:
  - domain-agent manifest readiness
  - provider trial/readiness evidence
  - grounding policy decision evidence
  - PromptOps version visibility evidence
  - MemoryOps retrieved-evidence posture
  - multi-turn eval gate evidence
- Return `go`, `review`, or `blocked` with machine-readable blockers, warnings, and recommended next action.
- Keep default `/api/chat` retrieval injection disabled.
- Keep provider invocation, answer generation, source binding creation, and GraphRAG execution out of scope.

## Capabilities

### New Capabilities

- `domain-agent-grounded-answer-promotion-gate`: caller-owned trial promotion decision for domain-agent grounded answer paths.

### Modified Capabilities

- `agent-grounding-policy`: clarify that grounding decisions are consumed by a higher-level promotion gate before behavior-affecting answer paths are trialed.
- `multiturn-agent-evaluation-gate`: clarify that deterministic eval results can be used as promotion evidence while remaining side-effect-free.
- `unified-knowledge-capability-runtime`: clarify that provider trial success is only one input into domain-agent grounded answer promotion.

## Impact

- Backend: adds a compact read-only promotion service.
- Tests: adds focused unit tests for `go`, provider blocked, missing policy review, citation blocker, and GraphRAG blocker paths.
- Docs/specs: records the stage boundary and non-goals.
- Runtime behavior: no default chat behavior change, no provider invocation, no answer generation, no mutation.
