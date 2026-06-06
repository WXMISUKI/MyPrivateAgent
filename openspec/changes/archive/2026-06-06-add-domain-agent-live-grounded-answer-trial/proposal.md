## Why

MyPrivateAgent has closed the external knowledge provider access path with a real local `unifiedKnowledgeRAG` trial. It also has Grounding Policy, PromptOps, MemoryOps, Multi-turn Eval, and domain-agent grounded-answer trial/package/composition control surfaces.

The remaining gap is a small explicit live trial that connects those pieces:

- read a domain agent manifest and its `rag_sources`
- call the external provider's document RAG retrieve endpoint
- consume the returned `evidence_pack`
- run the existing grounded-answer trial/package/composition chain
- return one `go / review / blocked` report

This proves a real provider evidence path for one domain agent without enabling default `/api/chat` retrieval injection.

## What Changes

- Add a side-effect-free `DomainAgentLiveGroundedAnswerTrialService`.
- Add a CLI script for local explicit trial execution.
- The live trial will:
  - validate the domain agent exists
  - require at least one manifest-declared RAG source
  - call `POST /api/rag/retrieve` on the configured provider
  - read `documents` and `metadata.evidence_pack`
  - pass the evidence into existing grounded-answer trial/package/composition services
  - report provider, trial, package, and composition status in one compact artifact
- Add focused tests using mocked provider transport.
- Update docs with the explicit live trial command.

## Capabilities

### New Capabilities

- `domain-agent-live-grounded-answer-trial`: explicit provider-backed domain-agent grounded-answer trial.

### Modified Capabilities

- `domain-agent-grounded-answer-trial-surface`: document that the live trial can feed real provider evidence into the existing trial surface.
- `unified-knowledge-capability-runtime`: document that live domain-agent trials may use the provider RAG retrieve contract, without changing default chat.

## Impact

- Affected code:
  - new service under `backend/services/`
  - new CLI script under `backend/scripts/`
- Affected tests:
  - focused backend tests for ready, insufficient-evidence, missing-agent/source, and provider failure cases
- Affected docs:
  - domain agent guide and external RAG provider guide
- No default runtime behavior changes.
- No source-to-agent binding, audit write, memory write, GraphRAG execution, or `/api/chat` retrieval injection.
