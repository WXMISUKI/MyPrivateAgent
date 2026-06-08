# Accept Local RAG Real Business Trial

## Why
The local RAG pipeline now supports real document upload-to-use trials and explicit question trials. The next step should not add another evidence layer or retrieval feature by assumption. It should run a compact real-business acceptance slice that tells the operator whether the current local RAG flow is usable, needs review, or is blocked.

## What Changes
- Add a local acceptance report that can combine:
  - one document upload-to-use result, and
  - a small set of explicit RAG question trial results.
- Provide a CLI exporter for the acceptance report.
- Classify follow-up into practical workstreams: operator flow, parser/OCR, citation/evidence, retrieval quality, or provider availability.
- Keep the acceptance loop read-only beyond the already explicit upload-to-use and question-trial inputs supplied by the operator.

## Roadmap Phase
Local RAG real business trial acceptance. This is a trigger-driven validation phase after the local RAG usable loop, not a continuation of provider readiness evidence.

## Non-Goals
- Do not enable default `/api/chat` retrieval injection.
- Do not create source-to-agent binding.
- Do not add GraphRAG, Qdrant, hybrid retrieval, rerank, or new parser engines.
- Do not start PaddleOCR, unifiedKnowledgeRAG, or MyPrivateAgent services.
- Do not build a full knowledge-base management UI.
- Do not write memory, audit, approval, trace, or governance records.
