# unified-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: Async document VLM invocation contract

The backend SHALL expose `document.vlm.parse.async` when VLM external provider is enabled.

#### Scenario: Async submit path and operation contract
- **GIVEN** the external VLM provider is enabled
- **WHEN** a client invokes `POST /api/capabilities/document.vlm.parse.async/invoke`
- **THEN** the request body MUST include `operation`.
- **AND** when `operation=submit`, the request MUST include `file_base64` and `media_type`.
- **AND** when `operation=status`, the request MUST include `job_id`.

### Requirement: Async result schema

The backend SHALL normalize async responses into:
- `job_id` (string)
- `status` in `queued|running|succeeded|failed|expired`
- `progress` (number)
- `result` (object, optional)
- `error` (object, optional)
- `warnings` (string array)
- `raw` (object)

### Requirement: Status normalization

The backend SHALL normalize raw provider status values:
- `success`, `done` -> `succeeded`
- `error`, `exception`, `timeout` -> `failed`
- `init`, `pending` -> `queued`
- unrecognized non-empty raw statuses -> `failed`

### Requirement: Provider path configuration

The backend SHALL read and apply:
- `VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH` (default `/api/vlm/jobs`)
- `VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE` (default `/api/vlm/jobs/{job_id}`)

### Requirement: Async error behavior

- If `status` is missing for `operation=status`, return `VLM_ASYNC_MISSING_JOB_ID`.
- If `operation` is unknown, return `VLM_ASYNC_INVALID_OPERATION`.
