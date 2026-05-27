# Change: unified-capability-runtime-registry

## Why
Voice, OCR, multimodal inference, video generation, and future AI capabilities have different dependency, runtime, and deployment constraints. The control plane should not import every heavy provider directly into the main backend process. We need a unified capability registry and invocation surface that can manage local providers today and external HTTP/MCP services later.

## What Changes
- Add a backend capability runtime registry with provider-neutral capability contracts.
- Expose stable API endpoints for capability discovery, health, and short synchronous invocation.
- Register the existing voice ASR/TTS runtime as local capabilities without moving it to a separate service yet.
- Add a frontend `capabilityApi` wrapper so UI and future domain agents do not call provider-specific endpoints directly.
- Document the future migration path from local provider to external service provider.

## 收口对象
- `backend/capability_runtime/` contracts, registry, service, local provider bridge.
- `backend/routers/capabilities.py` API surface.
- Router registration and frontend API wrapper.
- Docs and OpenSpec canonical spec.

## 非目标
- Do not create separate OCR/video/voice service projects in this slice.
- Do not remove or break the existing `/api/voice/*` endpoints.
- Do not add database-backed job persistence yet.
- Do not implement long-running video/OCR execution.
- Do not introduce provider-specific heavy dependencies into the default backend package.

## Impacted Contracts
- New:
  - `GET /api/capabilities`
  - `GET /api/capabilities/{capability_id}`
  - `GET /api/capabilities/{capability_id}/health`
  - `POST /api/capabilities/{capability_id}/invoke`
- Existing voice runtime remains a provider implementation detail and is exposed through the new registry.
