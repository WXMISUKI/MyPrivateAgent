# Proposal: Document RAG Local Operator Entrypoint

## Summary

Add a minimal MyPrivateAgent-side operator entrypoint for local document RAG trials. The entrypoint wraps the existing local readiness check and upload-to-use loop behind backend APIs and a small Settings diagnostics panel so a local operator can check readiness, run a real document trial, and inspect `go / review / blocked` results without manually stitching scripts together.

## Roadmap Phase

This follows the completed `document-rag-local-readiness` and `document-rag-upload-to-use-loop` slices. It advances local usability of real document RAG while preserving the project boundary that external OCR and unifiedKnowledgeRAG remain separate providers.

## Problem

The current local document RAG workflow is functional but script-oriented:

- run readiness CLI
- run upload-to-use CLI
- inspect generated report files
- remember OCR profile, timeout, provider URL, source id, and provider repo command

That is acceptable for development, but not yet a natural MyPrivateAgent local operator workflow.

## Goals

- Expose a backend readiness API for local document RAG trials.
- Expose a backend local trial API that runs readiness first and only runs upload-to-use when readiness is not blocked.
- Surface the entrypoint in Settings diagnostics with path/source/profile fields and compact result display.
- Return report paths, source id, decision, reason, and raw JSON for local debugging.
- Preserve all current runtime boundaries.

## Non-Goals

- Do not build a full knowledge-base management page.
- Do not use browser file upload for this slice; local operator path input is sufficient.
- Do not enable default `/api/chat` retrieval injection.
- Do not create source-to-agent bindings.
- Do not write memory, audit, approval, or governance records.
- Do not start PaddleOCR or unifiedKnowledgeRAG services.
- Do not introduce background queues or batch document management.
- Do not execute GraphRAG.

## Expected Outcome

A local operator can use MyPrivateAgent Settings diagnostics to:

1. Check document RAG local readiness.
2. Run a local document RAG trial for a real local document path.
3. See `go / review / blocked`, reason, source id, and report paths.
