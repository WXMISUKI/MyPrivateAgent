## Design Summary

`document.layout.parse` is a separate capability family under the same provider-neutral runtime.

Input envelope:
- `file_base64`, `media_type`, `filename`
- `output_format` (`markdown` or `json`)
- `include_tables`, `include_layout`, `max_pages`

Output envelope:
- `markdown`
- `elements[]`
- `tables[]`
- `pages[]`
- `artifacts[]`
- `warnings[]`
- `raw`

## Boundaries

- MyPrivateAgent remains control plane (contract, invoke, heartbeat, diagnostics).
- External provider remains data plane (PP-StructureV3 execution, heavy runtime, rendering, model files).
- No long-running job API in this slice; synchronous-only with explicit file-size/page limits.

## Verification

- Focused backend tests for request mapping and output normalization.
- Focused frontend diagnostics rendering tests for layout output.
