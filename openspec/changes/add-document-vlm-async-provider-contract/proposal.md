## Why

`document.vlm.parse` currently covers synchronous semantics only.
We already run async placeholder flow in practice (`document.vlm.parse.async`), but status endpoints, result status semantics, and operational errors are not yet frozen in the spec.

This change standardizes the async VLM provider contract before the project enters heavy async rollout.

## What Changes

- Formalize `document.vlm.parse.async` as a documented capability contract.
- Fix capability-level behavior for async submit/status operations:
  - `operation=submit`
  - `operation=status`
- Add configurable async endpoint metadata and env toggles.
- Normalize async status into a bounded set (`queued`, `running`, `succeeded`, `failed`, `expired`).
- Update backend env mapping and tests to prevent path regression and status regression.

## Impact

- Capability runtime:
  - `document_vlm_http_provider` supports configurable submit/status paths for async mode.
  - async status normalization and warning/fallback behavior are stable.
- Operations and ops runbook:
  - `.env` and capability configuration include async path controls.
- Docs/spec:
  - OpenSpec delta for unified capability runtime.
  - Frontend diagnostics behavior can rely on deterministic status text.
