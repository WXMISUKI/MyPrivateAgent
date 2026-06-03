## Design Summary

`document.vlm.parse.async` is modeled as an async control surface under the same VLM provider family.

Input envelope:
- `operation` (`submit` | `status`)
- `job_id` (required when `operation=status`)
- `file_base64`, `media_type`, `filename`, `task`, `question`, `max_pages` (required when `operation=submit`)

Output envelope (normalized result):
- `job_id`
- `status` in `queued|running|succeeded|failed|expired`
- `progress`
- `result`
- `error`
- `warnings`
- `raw`

Configurable async provider paths:
- `VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH` defaults to `/api/vlm/jobs`
- `VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE` defaults to `/api/vlm/jobs/{job_id}`

Status normalization:
- `success|done -> succeeded`
- `error|exception|timeout -> failed`
- `init|pending -> queued`
- other unrecognized non-empty statuses -> `failed` (stable fallback)
