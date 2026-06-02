# Document VLM Contract Freeze (Stage 3A)

## Scope

Stage 3A only freezes the `document.vlm.parse` contract and placeholder behavior.
No heavy VLM async pipeline or production throughput optimization is included in this stage.

## Runtime Toggles

```env
ENABLE_VLM_CAPABILITY_PROVIDER=true
VLM_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8080
VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=90
VLM_CAPABILITY_PROVIDER_INVOKE_PATH=/vlm
```

## Request Contract (Frozen)

Required fields:

- `file_base64`
- `media_type`
- `task`

Optional fields:

- `filename`
- `question`
- `max_pages`

Allowed `media_type`:

- `application/pdf`
- `image/png`
- `image/jpeg`

Allowed `task`:

- `summarize`
- `extract_fields`
- `chart_understanding`
- `qa`

Task-specific rule:

- `task=qa` requires non-empty `question`.

## Response Contract (Frozen)

The normalized result envelope is fixed as:

- `summary`
- `sections`
- `entities`
- `answers`
- `evidence`
- `warnings`
- `raw`

## Error Codes (Frozen)

- `VLM_INVALID_INPUT`
  - missing `file_base64`
  - invalid `max_pages` (non-positive)
  - missing `question` when `task=qa`
- `VLM_UNSUPPORTED_MEDIA_TYPE`
  - unsupported `media_type`
- `VLM_UNSUPPORTED_TASK`
  - unsupported `task`
- `DOCUMENT_VLM_PROVIDER_ERROR`
  - provider responded with non-zero `errorCode`
- transport/network errors
  - propagated as runtime provider transport errors

## Verification Baseline

```powershell
python -m pytest tests/agent_framework/test_capability_http_provider.py -q
```

Pass criteria for Stage 3A:

- Contract fields are stable in registry and invoke results.
- Validation and error codes are deterministic.
- No async job protocol is introduced in this stage.
