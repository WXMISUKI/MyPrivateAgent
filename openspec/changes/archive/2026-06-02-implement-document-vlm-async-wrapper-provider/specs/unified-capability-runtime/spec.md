# unified-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: Local async VLM wrapper provider

The project SHALL provide an optional local development provider that implements the `document.vlm.parse.async` job API for Stage 3B acceptance.

#### Scenario: Wrapper health is available
- **WHEN** the wrapper provider is running
- **AND** a client requests `GET /health`
- **THEN** the response includes `errorCode=0`
- **AND** the response includes provider configuration metadata for upstream base URL and invoke path.

#### Scenario: Async job submission
- **WHEN** a client requests `POST /api/vlm/jobs`
- **AND** the body includes `file`, `fileType`, and `task`
- **THEN** the wrapper returns `result.job_id`
- **AND** `result.status` is `queued` or `running`
- **AND** `result.progress` is a number.

#### Scenario: Async job polling
- **WHEN** a client requests `GET /api/vlm/jobs/{job_id}`
- **THEN** the wrapper returns `result.job_id`
- **AND** `result.status` is one of `queued`, `running`, `succeeded`, `failed`
- **AND** completed jobs expose either `result.result` or `result.error`.

#### Scenario: Missing job
- **WHEN** a client requests an unknown job id
- **THEN** the wrapper returns HTTP 404
- **AND** the body includes `errorCode`
- **AND** the error message identifies the missing job id.

#### Scenario: Upstream sync provider failure
- **WHEN** upstream document parsing fails
- **THEN** the wrapper keeps the job queryable
- **AND** marks the job as `failed`
- **AND** includes structured error detail in `result.error`.
