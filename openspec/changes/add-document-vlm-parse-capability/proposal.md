## Why

OCR and layout parsing cover text extraction and structure recovery, but multimodal document understanding needs a distinct semantic capability. A dedicated contract prevents conflating VLM reasoning with deterministic OCR/layout outputs.

## What Changes

- Add a new capability contract: `document.vlm.parse`.
- Define provider-neutral VLM output for semantic sections, chart understanding, and evidence references.
- Keep VLM integration as external provider only.
- Plan for async/job-mode follow-up when runtime exceeds synchronous SLA.

## Impact

- Backend capability runtime: new capability registration and invoke envelope.
- Frontend diagnostics: VLM invocation panel with semantic result and evidence rendering.
- Governance/docs: update capability taxonomy and usage boundaries.
