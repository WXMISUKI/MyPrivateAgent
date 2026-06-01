# Document Layout Capability Debug Guide

## Scope

This guide describes how to debug `document.layout.parse` in MyPrivateAgent capability diagnostics.

## Runtime Toggles

Set these in `.env`:

```env
ENABLE_LAYOUT_CAPABILITY_PROVIDER=true
LAYOUT_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8081
LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=60
LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH=/layout-parsing
```

## Request Fields

Diagnostics panel sends:

- `file_base64` (required)
- `media_type` (required): `application/pdf` or `image/png` or `image/jpeg`
- `filename`
- `output_format`: `markdown` or `json`
- `include_tables`: boolean
- `include_layout`: boolean
- `max_pages`: optional positive integer

## Expected Result Envelope

`document.layout.parse` returns:

- `markdown`
- `elements[]`
- `tables[]`
- `pages[]`
- `artifacts[]`
- `warnings[]`
- `raw`

## Common Error Codes

- `LAYOUT_INVALID_INPUT`: missing `file_base64` or invalid `max_pages`
- `LAYOUT_UNSUPPORTED_MEDIA_TYPE`: unsupported `media_type`
- `LAYOUT_INVALID_OUTPUT_FORMAT`: `output_format` is not `markdown|json`
- `PADDLE_LAYOUT_PROVIDER_ERROR`: provider returned non-zero `errorCode`
- `CAPABILITY_PROVIDER_UNREACHABLE`: provider endpoint is unreachable

## Quick Verification

```powershell
python -m pytest tests/agent_framework/test_capability_http_provider.py -q
cd frontend-vue
npm run test -- CapabilityProviderDiagnosticsPanel
```
