# Proposal: Document RAG Upload File Operator Entrypoint

## Summary

Extend the existing MyPrivateAgent local document RAG operator entrypoint so a local user can upload a document file from Settings diagnostics and run the existing readiness plus upload-to-use loop without manually supplying a browser-inaccessible absolute file path.

## Roadmap Phase

This follows the completed `document-rag-local-operator-entrypoint` slice. It improves local usability of the real document RAG path while preserving the external-provider boundary: OCR/Layout parsing and unifiedKnowledgeRAG ingestion remain provider-owned data-plane work.

## Problem

The current local operator API accepts only `document_path`. That works for developer scripts, but it is awkward from a browser UI because a selected file does not expose a reliable local absolute path to JavaScript. The Settings card therefore still requires the user to paste a path manually, even though the surrounding diagnostics already support file upload payloads.

## Goals

- Allow `POST /api/document-rag/local-trials` to accept either:
  - `document_path`, or
  - `file_base64` plus `filename` and `media_type`.
- Materialize uploaded file bytes into a controlled local operator upload directory before reusing the existing upload-to-use loop.
- Surface a file picker in the Settings diagnostics local document RAG card.
- Keep the existing local path mode for advanced/debug usage.
- Return upload materialization metadata in the operator result summary.
- Preserve all current runtime and ownership boundaries.

## Non-Goals

- Do not build a full knowledge-base management page.
- Do not enable default `/api/chat` retrieval injection.
- Do not create source-to-agent bindings.
- Do not write memory, audit, approval, or governance records.
- Do not start PaddleOCR, Layout, VLM, or unifiedKnowledgeRAG services.
- Do not introduce background queues, multi-file batch management, or retention policy UI.
- Do not execute GraphRAG.

## Expected Outcome

A local user can open Settings diagnostics, select a PDF/image file, run the local document RAG trial, and inspect `go / review / blocked`, readiness/trial decisions, source id, report paths, and materialized upload metadata.
