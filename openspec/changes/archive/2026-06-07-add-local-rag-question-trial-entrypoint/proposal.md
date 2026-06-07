# Add Local RAG Question Trial Entrypoint

## Why
The local document RAG flow can now check readiness, upload a real document, and confirm provider-side corpus availability. The next lightweight step is to let a local operator ask one business question against an already-ingested `source_id` from MyPrivateAgent without wiring the capability into default chat.

This keeps the project moving toward usable local knowledge-base trials while avoiding another provider evidence-only phase.

## What Changes
- Add a minimal backend local RAG question trial entrypoint.
- Expose the entrypoint through the existing document RAG local trial router.
- Extend the Settings diagnostics card with a question input and a trial action.
- Return a compact go/review/blocked result containing answer status, answer text, citations, evidence status, and report paths.

## Roadmap Phase
MyPrivateAgent local business RAG user loop: explicit local question trial after document upload-to-use succeeds.

## Non-Goals
- Do not inject retrieval into `/api/chat`.
- Do not create source-to-agent binding.
- Do not write memory, audit, approval, or governance records.
- Do not mutate domain-agent manifests.
- Do not start external services.
- Do not introduce GraphRAG or vector backend promotion.
