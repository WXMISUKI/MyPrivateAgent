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

The backend SHALL normalize async responses into a stable provider-neutral async envelope.

#### Scenario: Async response includes stable fields
- **WHEN** a client submits or checks a `document.vlm.parse.async` job
- **THEN** the normalized response MUST include `job_id`, `status`, `progress`, `warnings`, and `raw`.
- **AND** `status` MUST be one of `queued`, `running`, `succeeded`, `failed`, or `expired`.
- **AND** `result` MAY be present when parsing succeeds.
- **AND** `error` MAY be present when parsing fails.

### Requirement: Status normalization

The backend SHALL normalize raw provider status values into the accepted async status set.

#### Scenario: Successful provider status is normalized
- **WHEN** provider status is `success` or `done`
- **THEN** normalized status MUST be `succeeded`.

#### Scenario: Failed provider status is normalized
- **WHEN** provider status is `error`, `exception`, or `timeout`
- **THEN** normalized status MUST be `failed`.

#### Scenario: Queued provider status is normalized
- **WHEN** provider status is `init` or `pending`
- **THEN** normalized status MUST be `queued`.

#### Scenario: Unknown provider status fails closed
- **WHEN** provider status is unrecognized and non-empty
- **THEN** normalized status MUST be `failed`.

### Requirement: Provider path configuration

The backend SHALL read and apply configurable async provider paths.

#### Scenario: Default async provider paths are used
- **WHEN** async provider path environment variables are unset
- **THEN** the submit path MUST default to `/api/vlm/jobs`.
- **AND** the status path template MUST default to `/api/vlm/jobs/{job_id}`.

#### Scenario: Custom async provider paths are applied
- **WHEN** `VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH` or `VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE` is configured
- **THEN** the backend MUST use the configured path values for async submit and status requests.

### Requirement: Async error behavior

The backend MUST return stable async VLM error codes for invalid async operations.

#### Scenario: Missing async job id is rejected
- **WHEN** `operation=status` and `job_id` is missing
- **THEN** response `error.code` MUST be `VLM_ASYNC_MISSING_JOB_ID`.

#### Scenario: Unknown async operation is rejected
- **WHEN** `operation` is not `submit` or `status`
- **THEN** response `error.code` MUST be `VLM_ASYNC_INVALID_OPERATION`.
