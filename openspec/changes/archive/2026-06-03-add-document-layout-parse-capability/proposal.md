## Why

`document.ocr.extract` now covers base OCR extraction, but complex PDF layout, section structure, and table parsing need a dedicated capability contract. Reusing the OCR endpoint for layout output would blur semantics and make downstream workflows unstable.

## What Changes

- Add a new capability contract: `document.layout.parse`.
- Keep `document.ocr.extract` unchanged as base text extraction.
- Define provider-neutral output for markdown, layout elements, tables, and artifacts.
- Introduce diagnostics test affordance for layout parse payload/result inspection.

## Impact

- Backend capability runtime:
  - add capability registration path for `document.layout.parse` (external provider only).
  - add request/response normalization for layout payloads.
- Frontend diagnostics:
  - add layout-specific invoke test section and result rendering.
- Docs/spec:
  - extend unified capability runtime spec with layout parse requirements.
