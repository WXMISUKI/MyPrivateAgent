## 1. Stable Direction

- [x] 1.1 Add `provider-capability-roadmap` OpenSpec delta.
- [x] 1.2 Record P0/P1/P2 work as stable future change requirements.
- [x] 1.3 Clarify that the active RAG / GraphRAG provider line remains `plan-external-rag-graphrag-provider`.

## 2. External Provider Readiness

- [x] 2.1 Document that MyPrivateAgent should not implement provider internals in the main backend.
- [x] 2.2 Define external provider readiness gates before caller-side integration.
- [x] 2.3 Split next-stage RAG / GraphRAG work into contract/readiness, document RAG, graph discovery/query, and runtime promotion phases.

## 3. Follow-up Change Queue

- [x] 3.1 Record `add-agent-grounding-policy-contract` as P0 follow-up.
- [x] 3.2 Record `add-promptops-versioned-prompt-contract` as P1 follow-up.
- [x] 3.3 Record `add-agent-memoryops-lifecycle-contract` as P1 follow-up.
- [x] 3.4 Record `add-multiturn-agent-evaluation-gate` as P1 follow-up.
- [x] 3.5 Record P2 directions for multimodal taxonomy, workflow/chatflow, enterprise connectors, and provider ops.

## 4. Verification and Archive

- [x] 4.1 Run `cmd /c openspec validate stabilize-provider-capability-roadmap --strict`.
- [x] 4.2 Run `cmd /c openspec validate --all --strict`.
- [x] 4.3 Archive after validation so the roadmap becomes canonical.
