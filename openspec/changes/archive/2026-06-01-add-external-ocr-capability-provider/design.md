# Design: External PaddleOCR Capability Provider

## Architecture

The first integration uses PaddleX serving directly:

```text
MyPrivateAgent /api/capabilities/document.ocr.extract/invoke
        |
        v
CapabilityRuntimeService
        |
        v
paddleocr_http_provider
        |
        v
PaddleOCR PaddleX serving /ocr
```

PaddleOCR remains responsible for model runtime, OCR pipeline configuration, PDF/image handling, GPU/CPU device selection, and Paddle dependencies. MyPrivateAgent only owns registration, health, invocation normalization, and governance visibility.

## Configuration

New environment variables:

```env
ENABLE_OCR_CAPABILITY_PROVIDER=false
OCR_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8080
OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=30
```

When enabled, the capability registry adds:

```text
document.ocr.extract
```

## Request Mapping

MyPrivateAgent accepts:

```json
{
  "file_base64": "...",
  "media_type": "image/png",
  "visualize": false
}
```

The provider sends PaddleX:

```json
{
  "file": "...",
  "fileType": 1,
  "visualize": false
}
```

`fileType = 0` is used for `application/pdf`; `fileType = 1` is used for images.

## Response Normalization

PaddleX returns `result.ocrResults[*].prunedResult`. The provider normalizes common OCR fields:

- `text`: newline-joined recognized text.
- `pages`: page-level compact text and average confidence.
- `blocks`: line/block items with page number, text, confidence, and bounding box when available.
- `raw`: original PaddleX `result` for debugging and later contract refinement.

## Failure Behavior

- Remote outage returns `CAPABILITY_PROVIDER_UNREACHABLE`.
- Nonzero PaddleX `errorCode` returns `PADDLEOCR_PROVIDER_ERROR`.
- Missing `file_base64` returns `OCR_INVALID_INPUT`.
- Startup must not fail if PaddleOCR is disabled or unreachable.

## Follow-up Boundary

PP-StructureV3, PaddleOCR-VL, long-running OCR jobs, artifact storage, upload UI, and MCP-based tool discovery require separate OpenSpec changes.
