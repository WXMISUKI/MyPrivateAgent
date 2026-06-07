# Proposal: Document RAG Local Readiness Check

## Summary

Add a lightweight local readiness exporter for the real document-to-RAG workflow. The exporter checks whether the local operator environment is ready to run document upload-to-use trials before spending time on OCR, parser artifact handoff, provider ingestion, or corpus verification.

## Roadmap Phase

This advances the local document RAG usability path after `document-rag-upload-to-use-loop`. It keeps the focus on local usable RAG rather than GraphRAG, default chat retrieval injection, or additional evidence-chain phases.

## Problem

The real PDF upload-to-use loop now works, but the local workflow still depends on multiple moving parts:

- PaddleOCR service on `127.0.0.1:8080`
- OCR CPU/GPU profile and timeout posture
- unifiedKnowledgeRAG provider service on `127.0.0.1:8020`
- provider repo command path and `GRAPHRAG` Python command
- parser artifact ingestion script
- provider source catalog visibility

When one piece is missing, the current failure is discovered late, often after a slow OCR call or a provider command attempt. This slows down local iteration and makes large PDF trials feel brittle.

## Goals

- Provide a single local command that emits `go / review / blocked` readiness.
- Check OCR provider reachability and expose CPU/GPU profile hints from caller configuration.
- Check knowledge provider health and optional source visibility.
- Check provider repo path, parser artifact ingestion script, and provider Python command availability.
- Recommend practical next actions, especially around timeout and GPU/CPU profile.
- Keep the report as local operator evidence and avoid mutating runtime state.

## Non-Goals

- Do not upload or parse documents.
- Do not start PaddleOCR, unifiedKnowledgeRAG, or MyPrivateAgent services.
- Do not call provider-side parser artifact ingestion.
- Do not enable default `/api/chat` retrieval injection.
- Do not create source-to-agent binding.
- Do not write memory, audit, approval, or governance records.
- Do not execute GraphRAG.
- Do not build a frontend document management UI.

## Expected Outcome

After this change, a local operator can run a quick readiness command before a real document trial and see whether the environment is ready, needs review, or is blocked.
