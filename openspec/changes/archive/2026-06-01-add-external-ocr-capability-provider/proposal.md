# Change: add-external-ocr-capability-provider

## Why

The user has downloaded PaddleOCR to `D:\AI\AIcode\PaddleOCR` and wants to connect it to MyPrivateAgent as an OCR capability. PaddleOCR already provides a PaddleX serving path that exposes `POST /ocr`, so MyPrivateAgent should adapt that external HTTP service through the existing capability runtime instead of importing PaddleOCR dependencies into the main backend.

## What Changes

- Add a `document.ocr.extract` capability when an external PaddleOCR provider is enabled.
- Map MyPrivateAgent's provider-neutral OCR invoke payload to PaddleX serving's `/ocr` payload.
- Normalize PaddleX OCR responses into compact text, pages, blocks, and raw evidence.
- Add provider health and heartbeat handling that survives provider outage.
- Update OCR provider documentation with the direct PaddleX serving route and smoke commands.

## 收口对象

- `backend/capability_runtime/providers/paddleocr_http_provider.py`
- `backend/capability_runtime/registry.py`
- `backend/config.py`
- `docs/guides/external_ocr_provider_development.md`
- `openspec/specs/unified-capability-runtime/spec.md`

## 非目标

- Do not install PaddleOCR, PaddlePaddle, PaddleX, CUDA, or model weights into MyPrivateAgent.
- Do not add OCR to default `/api/chat`.
- Do not build upload UI, document management, OCR job queue, or artifact storage in this slice.
- Do not use PaddleOCR MCP as the first integration path; MCP can be evaluated later for dynamic tool discovery.
- Do not implement PP-StructureV3 or PaddleOCR-VL markdown conversion in this slice.

## Verification

- Focused unit tests for PaddleOCR provider health, request mapping, response normalization, and unreachable handling.
- `openspec validate add-external-ocr-capability-provider --strict`.
