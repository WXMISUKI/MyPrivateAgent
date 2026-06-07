## Context

Current state:

- `DocumentIngestionService` can submit a PDF/image to `document.ocr.extract`, `document.layout.parse`, or `document.vlm.parse.async`, and persist compact artifacts.
- `unifiedKnowledgeRAG` can consume normalized parser artifacts through a local parser-artifact ingestion loop.
- MyPrivateAgent can verify provider-visible sources through `export_local_knowledge_provider_corpus_trial.py`.

The gap is orchestration. There is not yet a stable provider HTTP ingestion endpoint, so this slice should not pretend to be the final product upload API. It should provide a local, explicit trial loop that proves the full path and creates the contract surface for a later HTTP productization.

## Goals / Non-Goals

**Goals:**
- Start from a real local document file in MyPrivateAgent.
- Reuse existing document ingestion/artifact persistence.
- Convert OCR/Layout artifacts into a normalized parser artifact handoff compatible with unifiedKnowledgeRAG.
- Invoke the local provider-side parser artifact ingestion command when configured.
- Verify the resulting source through the existing provider corpus trial.
- Export one `go / review / blocked` report.

**Non-Goals:**
- Do not add a frontend upload UI.
- Do not add a stable HTTP `knowledge.document.ingest` API in this repo.
- Do not mutate default `/api/chat` behavior.
- Do not create source-to-agent bindings or domain-agent manifest changes.
- Do not start PaddleOCR or unifiedKnowledgeRAG services.
- Do not introduce background workers, queues, permissions, audit policy, or GraphRAG execution.
- Do not promote vector backends or retrieval defaults.

## Decisions

1. Use a local trial loop instead of a product API.

   The provider-side ingestion path is currently a CLI/local repo operation, not a provider HTTP contract. A local trial loop is honest about that boundary and avoids baking an unstable cross-repo API into MyPrivateAgent.

2. Reuse `DocumentIngestionService`.

   This avoids duplicating PaddleOCR invocation and artifact persistence logic. The new loop treats the document artifact as the stable source of parser output.

3. Emit a normalized parser artifact from MyPrivateAgent.

   The normalized artifact is the narrow handoff contract between caller orchestration and provider ingestion. It can later become the body of a future `knowledge.document.ingest` HTTP request.

4. Keep provider command execution injectable.

   Tests should not depend on a real unifiedKnowledgeRAG checkout or running services. The real command remains a local operator path.

## Risks / Trade-offs

- Provider ingestion is still command-based -> The report records `review` or `blocked` with the command result instead of claiming product readiness.
- OCR output quality may vary -> The loop blocks when no text blocks can be converted and recommends reviewing parser output.
- Cross-repo paths are local-machine specific -> The CLI requires explicit `--knowledge-provider-repo` and keeps this as local trial tooling.
- Large PDFs may be slow -> The loop forwards `max_pages` to existing ingestion where supported and keeps this as an explicit operator run.
