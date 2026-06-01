# External OCR Provider Development Guide

## 1. Positioning

OCR should be integrated as an external capability provider. MyPrivateAgent remains the runtime control plane and should not import PaddleOCR, Tesseract, EasyOCR, Surya, docTR, CUDA, model weights, document parsers, or PDF rendering dependencies into the main backend process.

```text
MyPrivateAgent
  owns capability registration, invocation envelope, policy, approval,
  trace, audit, provider health, diagnostics, and business integration.

External OCR Provider
  owns OCR engines, model files, image/PDF preprocessing, layout parsing,
  table extraction, page rendering, GPU/CPU runtime, batching, and artifacts.
```

The first production-friendly path for the local repository at `D:\AI\AIcode\PaddleOCR` is:

1. Run PaddleOCR/PaddleX serving independently.
2. Let PaddleX expose `POST /ocr`.
3. Register the service as `document.ocr.extract` in MyPrivateAgent.
4. Let RAG or domain-agent workflows consume OCR output through explicit artifacts or capability invocation.

## 2. Open Source Candidates

Current mature options:

| Project | Best fit | Strengths | Caveats |
|---|---|---|---|
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Recommended first choice for Chinese and document-heavy enterprise use | Strong Chinese and multilingual OCR, document parsing, table/formula/layout support, Apache 2.0, active ecosystem, agent/RAG integrations | Paddle/PaddleOCR runtime is heavier than simple OCR libraries; GPU setup should stay outside MyPrivateAgent |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | Lightweight fallback and classic printed text OCR | Mature, stable, Apache 2.0, easy to package, good for clean scans | Weaker on complex Chinese layouts, tables, handwriting, screenshots, and modern document understanding |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | Simple Python OCR provider prototype | Easy to start, supports many scripts including Chinese, Apache 2.0 | Less complete for structured PDF/document parsing; slower and less controllable for enterprise batch workflows |
| [docTR](https://github.com/mindee/doctr) | Clean FastAPI-style OCR service prototype | Deep-learning OCR, Apache 2.0, includes an API template and Docker path | More text detection/recognition oriented; less document-intelligence complete than PaddleOCR |
| [Surya](https://github.com/datalab-to/surya) | High-quality document intelligence and layout/table recognition trial | Strong OCR/layout/reading-order/table recognition, modern document VLM path | Model weights have commercial-use constraints; check licensing before enterprise use |

Recommended decision:

- Start with PaddleOCR as the primary provider candidate.
- Keep Tesseract as an optional lightweight fallback for clean printed text.
- Use docTR or EasyOCR only if PaddleOCR deployment is too heavy for the first local smoke.
- Evaluate Surya only after licensing and GPU/runtime constraints are acceptable.

## 3. Capability Contract

Proposed capability id:

```text
document.ocr.extract
```

Proposed capability metadata:

```json
{
  "capability_id": "document.ocr.extract",
  "kind": "ocr",
  "transport": "http",
  "provider": "external_ocr_provider",
  "status": "ready",
  "input_schema": {
    "type": "object",
    "required": ["file_base64", "media_type"],
    "properties": {
      "file_base64": { "type": "string" },
      "media_type": { "type": "string" },
      "filename": { "type": "string" },
      "language_hints": { "type": "array", "items": { "type": "string" } },
      "output_format": { "type": "string", "enum": ["plain_text", "json", "markdown"] },
      "include_layout": { "type": "boolean" },
      "include_tables": { "type": "boolean" },
      "max_pages": { "type": "integer" }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "text": { "type": "string" },
      "pages": { "type": "array" },
      "blocks": { "type": "array" },
      "tables": { "type": "array" },
      "artifacts": { "type": "array" },
      "warnings": { "type": "array" }
    }
  }
}
```

Use `POST /api/capabilities/document.ocr.extract/invoke` only for small synchronous files. Large PDFs, batch OCR, high-resolution image sets, or long document parsing should use provider-owned job endpoints and return an artifact reference.

## 4. PaddleOCR Service Startup

PaddleOCR recommends using PaddleX serving for service deployment. In a separate Python environment for PaddleOCR:

```powershell
cd D:\AI\AIcode\PaddleOCR
pip install -e .
paddlex --install serving
paddlex --serve --pipeline OCR --host 127.0.0.1 --port 8080
```

The service should expose:

```http
GET  http://127.0.0.1:8080/health
POST http://127.0.0.1:8080/ocr
```

PaddleX request example:

```json
{
  "file": "<base64 image or PDF>",
  "fileType": 1,
  "visualize": false
}
```

`fileType = 1` means image and `fileType = 0` means PDF.

PaddleOCR also provides an MCP server. That is useful for dynamic agent tool discovery, but MyPrivateAgent's first integration should use HTTP capability runtime because it already has health, heartbeat, invocation, diagnostics, and governance semantics.

## 5. Provider HTTP API

Generic provider API shape:

```http
GET  /health
GET  /api/capabilities
POST /api/ocr/extract
```

For the downloaded PaddleOCR project, MyPrivateAgent directly adapts PaddleX serving instead:

```http
POST /ocr
```

Recommended lifecycle API:

```http
POST /api/ocr/jobs
GET  /api/ocr/jobs/{job_id}
GET  /api/ocr/artifacts/{artifact_id}
```

The synchronous endpoint should accept:

```json
{
  "file_base64": "...",
  "media_type": "application/pdf",
  "filename": "case-file.pdf",
  "language_hints": ["zh", "en"],
  "output_format": "json",
  "include_layout": true,
  "include_tables": true,
  "max_pages": 10
}
```

The response should use a provider-neutral envelope:

```json
{
  "ok": true,
  "capability_id": "document.ocr.extract",
  "provider": "paddleocr",
  "result": {
    "text": "full compact text for model input",
    "pages": [
      {
        "page_number": 1,
        "text": "page text",
        "confidence": 0.94
      }
    ],
    "blocks": [
      {
        "page_number": 1,
        "block_id": "p1-b1",
        "type": "paragraph",
        "text": "recognized text",
        "bbox": [10, 20, 300, 80],
        "confidence": 0.92
      }
    ],
    "tables": [],
    "artifacts": [],
    "warnings": []
  }
}
```

Failures must be structured:

```json
{
  "ok": false,
  "capability_id": "document.ocr.extract",
  "provider": "paddleocr",
  "error": {
    "code": "OCR_UNSUPPORTED_MEDIA_TYPE",
    "message": "Only PDF, PNG, and JPEG are supported by this provider."
  }
}
```

## 6. MyPrivateAgent Wiring

`.env` shape:

```env
ENABLE_OCR_CAPABILITY_PROVIDER=true
OCR_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8080
OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=30
```

Expected MyPrivateAgent behavior:

- `GET /api/capabilities` lists `document.ocr.extract` only when OCR provider is enabled.
- `GET /api/capabilities/heartbeat` reports provider status without blocking the main server.
- `POST /api/capabilities/document.ocr.extract/invoke` delegates to PaddleX `POST /ocr` and returns a provider-neutral envelope.
- Provider outage returns `status=unreachable` and a machine-readable error, while `/api/chat` remains healthy.
- OCR result can later feed RAG ingestion, document question answering, image evidence extraction, or domain-agent tools through explicit workflows.

Invoke through MyPrivateAgent:

```powershell
$file = [Convert]::ToBase64String([IO.File]::ReadAllBytes("D:\path\demo.png"))
$payload = @{
  file_base64 = $file
  media_type = "image/png"
  visualize = $false
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/capabilities/document.ocr.extract/invoke" `
  -ContentType "application/json" `
  -Body $payload
```

The MyPrivateAgent adapter maps this to PaddleX:

```json
{
  "file": "<base64>",
  "fileType": 1,
  "visualize": false
}
```

and normalizes PaddleX `result.ocrResults[*].prunedResult` into:

```json
{
  "text": "recognized text",
  "pages": [],
  "blocks": [],
  "raw": {}
}
```

## 7. Recommended First Slice

First implementation should be intentionally small:

1. Run PaddleOCR as a PaddleX standalone service.
2. Use PaddleX `/ocr` directly.
3. Support PNG/JPEG first, then PDF.
4. Return plain text, page text, bounding boxes, confidence, and warnings.
5. Add MyPrivateAgent capability registration through the existing capability runtime.
6. Add one active test from the capability diagnostics panel.
7. Keep large PDF jobs and artifact storage out of the first slice.

OpenSpec should be created before implementation because this introduces a new capability family and external provider contract.

Suggested change name:

```text
add-external-ocr-capability-provider
```

Suggested spec deltas:

- `unified-capability-runtime`
- optional new `external-ocr-provider`
- optional `domain-agent-asset-registry` if domain agents declare OCR-enabled document sources

## 8. Verification

Provider-only smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health

$file = [Convert]::ToBase64String([IO.File]::ReadAllBytes("D:\path\demo.png"))
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8080/ocr" `
  -ContentType "application/json" `
  -Body (@{ file = $file; fileType = 1; visualize = $false } | ConvertTo-Json -Depth 8)
```

MyPrivateAgent smoke after wiring:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/capabilities
Invoke-RestMethod http://127.0.0.1:8000/api/capabilities/heartbeat
```

Focused backend verification should be added only for the provider registration and HTTP delegation path. Do not run a full frontend build for this slice unless UI contract changes are made.

## 9. Non-goals

- Do not install PaddleOCR, Tesseract, EasyOCR, Surya, docTR, CUDA, or model weights into the MyPrivateAgent backend environment.
- Do not make OCR a default part of `/api/chat`.
- Do not upload arbitrary business documents through MyPrivateAgent before permission, storage, and retention policies are defined.
- Do not treat OCR output as trusted facts without source, confidence, and artifact provenance.
- Do not build full document management, annotation, or training workflows in the control plane.

## 10. Notes on Image and Video Models

The existing capability runtime is already designed to support OCR, multimodal inference, and video generation as provider-neutral capabilities. The control plane can support these kinds, but concrete providers are not registered yet.

Future capability ids could include:

```text
image.vision.analyze
image.generate
image.edit
video.generate
video.understand
document.ocr.extract
```

Image and video generation should be treated as external HTTP job providers rather than synchronous chat features. They usually need long-running jobs, GPU scheduling, artifact storage, quota control, safety review, and audit records.
