# Layout Capability Acceptance Checklist

## Purpose

Validate `document.layout.parse` with a small real-sample set before broader rollout.

## Sample Set

Prepare 3 files:

- `sample-scan.pdf`: scanned PDF with noisy text
- `sample-table.pdf`: table-focused PDF
- `sample-image.jpg`: image document screenshot

## Environment

```env
ENABLE_LAYOUT_CAPABILITY_PROVIDER=true
LAYOUT_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8080
LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=60
```

## Functional Checks

1. Registry and heartbeat
- `GET /api/capabilities` includes `document.layout.parse`
- `GET /api/capabilities/heartbeat` provider status is `ready` or structured `unreachable`

2. Invocation basics
- Upload each sample from diagnostics panel
- Use `output_format=markdown`, `include_tables=true`, `include_layout=true`
- Verify response contains: `markdown/elements/tables/pages/artifacts/warnings/raw`

3. Quality expectations
- `sample-scan.pdf`: markdown is non-empty and section boundaries are mostly preserved
- `sample-table.pdf`: `tables[]` is non-empty and row/column structure is present in `raw`
- `sample-image.jpg`: elements contain expected paragraph/title-level blocks

4. Error behavior
- invalid media type -> `LAYOUT_UNSUPPORTED_MEDIA_TYPE`
- invalid output format -> `LAYOUT_INVALID_OUTPUT_FORMAT`
- invalid max pages -> `LAYOUT_INVALID_INPUT`

## Exit Criteria

- 3/3 samples return `ok=true`
- No unstructured backend errors
- Frontend can render markdown/tables/raw for all samples
- Known quality gaps are recorded in `warnings` or rollout notes
