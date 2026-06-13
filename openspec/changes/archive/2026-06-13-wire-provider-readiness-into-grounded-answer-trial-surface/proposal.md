## Why

`unifiedKnowledgeRAG` has reached the current local document RAG closure line and MyPrivateAgent already exposes provider `governance_readiness` plus promotion-gate consumption. The next highest-value step is to make the explicit grounded-answer trial surface preserve that readiness evidence end-to-end, so caller-side trial reports can explain provider-ready, degraded, unreachable, and GraphRAG-gated states without reopening provider internals.

## What Changes

- Extend the explicit grounded-answer trial report to carry compact provider governance readiness evidence when supplied by the caller.
- Align trial `go / review / blocked` posture with the existing promotion gate provider-readiness semantics.
- Preserve blockers and warnings for provider unreachable, source catalog degraded, and GraphRAG gated states.
- Keep the trial surface side-effect-free: no provider call, no `/api/chat` call, no answer generation, no source binding, no audit/memory/trace mutation.

收口对象：MyPrivateAgent caller-owned grounded-answer trial surface.

非目标：

- Do not optimize `unifiedKnowledgeRAG` retrieval strategy.
- Do not enable default `/api/chat` retrieval injection.
- Do not implement GraphRAG execution.
- Do not create source-to-agent binding automation.
- Do not generate final answers or model calls.
- Do not add a new provider dependency inside MyPrivateAgent core backend.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-agent-grounded-answer-trial-surface`: trial reports must preserve caller-supplied provider governance readiness evidence and reflect promotion-gate provider readiness outcomes.

## Impact

- Backend service: grounded-answer trial report assembly and normalization.
- Tests: focused domain-agent grounded-answer trial service coverage for provider ready, degraded, unreachable, and graph-gated states.
- Specs/docs: `domain-agent-grounded-answer-trial-surface`, runtime contracts, and next-phase hardening notes.
- APIs: no new endpoint is required; existing explicit trial surface response may gain compact readiness evidence fields.
