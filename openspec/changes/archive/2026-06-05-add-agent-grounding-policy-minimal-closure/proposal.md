## Why

The unified knowledge provider access path is now closed with a repo-side `go` decision, but MyPrivateAgent still needs a caller-owned grounding policy gate before any external RAG evidence can influence answer behavior. This phase turns the existing visibility-only grounding policy fields into a minimal, testable decision contract without enabling default `/api/chat` retrieval injection.

## What Changes

- Add the canonical `agent-grounding-policy` capability spec.
- Add a side-effect-free grounding policy decision service for domain-agent RAG evidence consumption.
- Keep the existing domain-agent manifest normalization and Runtime Surface visibility behavior.
- Require cited evidence when a policy declares `require_citations=true`.
- Fail closed for insufficient evidence when policy requires knowledge for a domain.
- Preserve GraphRAG execution as separately gated and not promoted by document RAG readiness.
- Keep default `/api/chat` retrieval injection disabled.

## Capabilities

### New Capabilities
- `agent-grounding-policy`: Caller-owned grounding policy and decision gate for whether external knowledge evidence may be used by an agent response path.

### Modified Capabilities
- `domain-agent-asset-registry`: Clarify canonical grounding policy manifest/readiness behavior.
- `unified-knowledge-capability-runtime`: Clarify that provider trial readiness does not enable default chat retrieval injection and that grounding policy decisions are caller-side.

## Impact

- Backend: adds a small read-only grounding policy decision service.
- Tests: adds focused unit tests for default-disabled behavior, citation requirements, insufficient evidence, and GraphRAG boundary.
- Docs/specs: synchronizes `agent-grounding-policy` into canonical OpenSpec and keeps provider/caller boundaries explicit.
- Runtime behavior: no default chat behavior change, no provider mutation, no source binding creation, no GraphRAG execution.
