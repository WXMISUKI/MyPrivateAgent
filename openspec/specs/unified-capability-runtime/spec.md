# unified-capability-runtime Specification

## Purpose
Defines the provider-neutral capability runtime registry for AI capabilities such as ASR, TTS, OCR, multimodal inference, and video generation. The registry lets MyPrivateAgent discover, health-check, and invoke local or external providers without binding frontend or agent code to provider-specific runtime environments.
## Requirements
### Requirement: Capability Registry Contract
The backend SHALL expose a provider-neutral capability registry for AI capabilities.

#### Scenario: Registry lists voice capabilities
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the response includes `contract_version`
- **AND** includes registered capabilities for `voice.tts.edge` and `voice.asr.vosk`
- **AND** each capability includes `capability_id`, `kind`, `transport`, `provider`, `status`, `input_schema`, and `output_schema`.

#### Scenario: Registry returns one capability
- **WHEN** a client requests `GET /api/capabilities/voice.tts.edge`
- **THEN** the response returns the matching capability contract
- **AND** does not expose provider internals beyond the contract.

#### Scenario: External voice provider registration
- **GIVEN** `ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true`
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** `voice.tts.edge` and `voice.asr.vosk` are exposed with `transport=http`
- **AND** their status is resolved from the configured external provider health endpoints.

#### Scenario: Legacy local voice fallback is explicit
- **GIVEN** no external voice provider is configured
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** local voice capabilities may be exposed as legacy fallback contracts
- **AND** their metadata indicates `voice_runtime` is a legacy local fallback rather than the recommended production provider.

### Requirement: Capability Health
The backend SHALL expose provider-neutral health for each capability.

#### Scenario: Health reports disabled or dependency status
- **WHEN** a client requests `GET /api/capabilities/voice.tts.edge/health`
- **THEN** the response returns the same status category used by the registry
- **AND** includes a human-readable reason when the capability is not ready.

#### Scenario: External provider unreachable
- **GIVEN** an HTTP capability provider is configured but unreachable
- **WHEN** a client requests capability health
- **THEN** the response reports `status=unreachable`
- **AND** includes an error code `CAPABILITY_PROVIDER_UNREACHABLE`.

### Requirement: Capability Invocation
The backend SHALL expose a short synchronous invocation endpoint for registered capabilities.

#### Scenario: Disabled capability invocation returns structured unavailable error
- **GIVEN** voice runtime is disabled
- **WHEN** a client posts to `POST /api/capabilities/voice.tts.edge/invoke`
- **THEN** the backend returns a structured unavailable error
- **AND** the main server remains healthy.

#### Scenario: Unknown capability returns not found
- **WHEN** a client posts to `POST /api/capabilities/unknown/invoke`
- **THEN** the backend returns a structured not-found error.

#### Scenario: External capability invocation delegates to provider
- **GIVEN** `voice.tts.edge` is registered as an HTTP capability
- **WHEN** a client posts to `POST /api/capabilities/voice.tts.edge/invoke`
- **THEN** the backend delegates the payload to the configured external provider invoke endpoint
- **AND** returns the provider-neutral response envelope.

### Requirement: Frontend Capability API Wrapper
The frontend SHALL provide a provider-neutral capability API wrapper.

#### Scenario: Frontend calls capability runtime
- **WHEN** frontend code calls `capabilityApi.list()`, `capabilityApi.get(id)`, `capabilityApi.health(id)`, `capabilityApi.heartbeat()`, or `capabilityApi.invoke(id, payload)`
- **THEN** requests go through the existing API base and auth interceptor.

### Requirement: Capability Provider Heartbeat
The backend SHALL expose a live heartbeat surface for external capability providers.

#### Scenario: Heartbeat reports provider and capability status
- **WHEN** a client requests `GET /api/capabilities/heartbeat`
- **THEN** the response includes `contract_version`
- **AND** includes provider heartbeat records
- **AND** includes per-capability health records for the provider.

#### Scenario: Heartbeat survives provider outage
- **GIVEN** an external capability provider is configured but unreachable
- **WHEN** a client requests `GET /api/capabilities/heartbeat`
- **THEN** the response still returns 200
- **AND** the provider record reports `status=unreachable`
- **AND** includes a machine-readable error code.

### Requirement: Capability Active Test Endpoint
The backend SHALL expose an active test endpoint for registered capabilities.

#### Scenario: TTS capability default test summarizes audio
- **GIVEN** `voice.tts.edge` is registered and callable
- **WHEN** a client posts to `POST /api/capabilities/voice.tts.edge/test` with an empty payload
- **THEN** the backend invokes the capability with a default test sentence
- **AND** returns `ok=true`, `status=ok`, `latency_ms`, and a result summary containing `media_type` and `audio_base64_length`.

#### Scenario: ASR capability without audio uses health-only mode
- **GIVEN** `voice.asr.vosk` is registered
- **WHEN** a client posts to `POST /api/capabilities/voice.asr.vosk/test` without `audio_base64`
- **THEN** the backend checks capability health only
- **AND** returns `mode=health_only` without claiming transcript success.

#### Scenario: Active test failure is structured
- **GIVEN** a provider is unreachable or returns an invocation error
- **WHEN** a client posts to the active test endpoint
- **THEN** the backend returns a structured error envelope
- **AND** the main server remains healthy.

### Requirement: Capability Diagnostics UI
The frontend SHALL expose a diagnostics panel for capability providers.

#### Scenario: Diagnostics panel loads registry and heartbeat
- **WHEN** the settings page renders the capability diagnostics panel
- **THEN** it requests the capability registry and heartbeat
- **AND** displays provider and capability status.

#### Scenario: Diagnostics panel runs capability tests
- **WHEN** a user clicks a capability test action
- **THEN** the panel calls `capabilityApi.test`
- **AND** displays success, latency, summaries, or structured errors inline.

### Requirement: Realtime ASR Stream Proxy
The backend SHALL expose a provider-neutral realtime stream proxy for ASR capabilities.

#### Scenario: Realtime stream uses configured external provider
- **GIVEN** `voice.asr.vosk` is registered as an HTTP external provider capability
- **WHEN** a browser opens `WS /api/capabilities/voice.asr.vosk/stream`
- **THEN** the backend proxies binary audio chunks and text control frames to the provider stream endpoint
- **AND** forwards provider transcript messages back to the browser.

#### Scenario: Realtime stream reports unavailable provider
- **GIVEN** `voice.asr.vosk` has no external stream endpoint or provider connection fails
- **WHEN** a browser opens the realtime stream endpoint
- **THEN** the backend sends a structured ASR stream error message
- **AND** closes the WebSocket without affecting the main server.

### Requirement: Chat Microphone Uses Managed Realtime ASR
The frontend SHALL use the managed realtime ASR stream for the main chat microphone when available.

#### Scenario: Main chat streams microphone audio to ASR
- **GIVEN** `voice.asr.vosk` health is `ready`
- **WHEN** the user clicks the main chat microphone button
- **THEN** the frontend captures microphone audio
- **AND** sends 16kHz mono PCM s16le chunks to the MyPrivateAgent ASR stream endpoint
- **AND** writes partial and final transcript messages into the existing textarea.

#### Scenario: Main chat preserves existing send flow
- **GIVEN** realtime ASR has written text into the textarea
- **WHEN** the user sends the message
- **THEN** the existing conversation send flow is used
- **AND** no new `/api/chat` request fields are required.

#### Scenario: Managed ASR fallback
- **GIVEN** managed ASR is not ready or cannot start
- **WHEN** browser `SpeechRecognition` is available
- **THEN** the microphone button falls back to browser speech recognition
- **AND** user-entered text is preserved.

### Requirement: External knowledge provider registration
The backend SHALL be able to register external Knowledge Provider capabilities through the unified capability runtime.

#### Scenario: Knowledge provider registration is enabled
- **GIVEN** an external knowledge provider is configured
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** `knowledge.rag.retrieve` and `knowledge.graph.query` are exposed with `transport=http`
- **AND** their status is resolved from the configured provider health endpoints

#### Scenario: Knowledge provider heartbeat survives outage
- **GIVEN** an external knowledge provider is configured but unreachable
- **WHEN** a client requests `GET /api/capabilities/heartbeat`
- **THEN** the response still returns 200
- **AND** the provider record reports `status=unreachable`
- **AND** includes a machine-readable error code

### Requirement: External PaddleOCR provider registration

The backend SHALL register `document.ocr.extract` as an HTTP OCR capability when an external PaddleOCR provider is configured.

#### Scenario: OCR provider registration is enabled

- **GIVEN** `ENABLE_OCR_CAPABILITY_PROVIDER=true`
- **AND** `OCR_CAPABILITY_PROVIDER_BASE_URL` is configured
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the response includes `document.ocr.extract`
- **AND** the capability has `kind = ocr`
- **AND** the capability has `transport = http`

#### Scenario: OCR provider is unavailable

- **GIVEN** the OCR provider is configured but unreachable
- **WHEN** a client requests capability health or heartbeat
- **THEN** the backend reports `status = unreachable`
- **AND** includes a machine-readable provider error
- **AND** the main server remains healthy

### Requirement: PaddleX OCR response normalization

The OCR capability SHALL map provider-neutral invoke requests to PaddleX serving and normalize PaddleX OCR responses into a compact provider-neutral envelope.

#### Scenario: OCR invocation succeeds

- **WHEN** a client invokes `POST /api/capabilities/document.ocr.extract/invoke`
- **THEN** the backend sends the file payload to PaddleX serving `POST /ocr`
- **AND** maps image media types to `fileType = 1`
- **AND** maps `application/pdf` to `fileType = 0`
- **AND** the response includes `text`, `pages`, `blocks`, and `raw` evidence

#### Scenario: OCR invocation input is missing

- **WHEN** a client invokes OCR without `file_base64`
- **THEN** the backend returns `ok = false`
- **AND** returns error code `OCR_INVALID_INPUT`

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

### Requirement: Document Artifact Persistence Contract

The backend SHALL expose a local document artifact contract for compact OCR/Layout/VLM capability outputs.

#### Scenario: Persist compact document artifact
- **WHEN** a client posts `POST /api/document-artifacts`
- **AND** the request includes `capability_id`, `provider`, and `result`
- **THEN** the backend persists compact artifact metadata and payload
- **AND** returns `ok=true`
- **AND** returns `artifact.artifact_id`
- **AND** returns `artifact.content_hash`.

#### Scenario: Raw provider payload is excluded by default
- **WHEN** the result contains a `raw` field
- **AND** `include_raw` is not true
- **THEN** the persisted payload MUST NOT include `raw`.

#### Scenario: Read document artifact
- **WHEN** a client requests `GET /api/document-artifacts/{artifact_id}`
- **THEN** the backend returns metadata and compact payload for that artifact.

#### Scenario: List document artifacts
- **WHEN** a client requests `GET /api/document-artifacts`
- **THEN** the backend returns a list of artifact metadata records sorted newest first.

#### Scenario: Unknown artifact id
- **WHEN** a client requests an unknown artifact id
- **THEN** the backend returns HTTP 404
- **AND** returns error code `DOCUMENT_ARTIFACT_NOT_FOUND`.

### Requirement: Diagnostics Artifact Action

The frontend diagnostics panel SHALL allow users to persist successful document capability results on demand.

#### Scenario: Persist action appears for successful document result
- **WHEN** OCR/Layout/VLM diagnostics result is successful
- **THEN** the panel exposes a persist artifact action.

#### Scenario: Persist action returns artifact id
- **WHEN** a user persists a successful result
- **THEN** the panel calls `POST /api/document-artifacts`
- **AND** displays the returned `artifact_id`.

### Requirement: Document Ingestion Workflow Contract

The backend SHALL expose a document ingestion workflow that orchestrates existing document capabilities and persists successful outputs as artifacts.

#### Scenario: Submit OCR ingestion
- **WHEN** a client posts `POST /api/document-ingestions`
- **AND** the request includes `parse_mode=ocr`, `file_base64`, `media_type`, and `filename`
- **THEN** the backend invokes `document.ocr.extract`
- **AND** persists a compact document artifact on success
- **AND** returns `ok=true`
- **AND** returns `ingestion.ingest_id`
- **AND** returns `ingestion.artifact_id`.

#### Scenario: Submit Layout ingestion
- **WHEN** a client posts `POST /api/document-ingestions`
- **AND** the request includes `parse_mode=layout`, `file_base64`, `media_type`, and `filename`
- **THEN** the backend invokes `document.layout.parse`
- **AND** forwards layout options such as `output_format`, `include_tables`, `include_layout`, and `max_pages`
- **AND** persists a compact document artifact on success.

#### Scenario: Submit async VLM ingestion
- **WHEN** a client posts `POST /api/document-ingestions`
- **AND** the request includes `parse_mode=vlm_async`, `file_base64`, `media_type`, and `filename`
- **THEN** the backend invokes `document.vlm.parse.async`
- **AND** records provider job metadata when the provider returns a non-terminal job
- **AND** persists a compact document artifact when a terminal successful result is available.

#### Scenario: Read ingestion status
- **WHEN** a client requests `GET /api/document-ingestions/{ingest_id}`
- **THEN** the backend returns persisted ingestion metadata including status, parse mode, provider, warnings, error, and artifact reference.

#### Scenario: Read ingestion result
- **WHEN** a client requests `GET /api/document-ingestions/{ingest_id}/result`
- **AND** the ingestion has an artifact reference
- **THEN** the backend returns ingestion metadata, artifact metadata, and compact artifact payload.

#### Scenario: Unknown ingestion id
- **WHEN** a client requests an unknown ingestion id
- **THEN** the backend returns HTTP 404
- **AND** returns error code `DOCUMENT_INGEST_NOT_FOUND`.

#### Scenario: Invalid ingestion input
- **WHEN** a client submits an unsupported parse mode or missing required document payload
- **THEN** the backend returns HTTP 400
- **AND** returns error code `DOCUMENT_INGEST_INVALID_INPUT`.

### Requirement: Document Ingestion Diagnostics Action

The frontend diagnostics panel SHALL expose a minimal document ingestion test area for local provider orchestration.

#### Scenario: Submit ingestion from diagnostics
- **WHEN** a user selects a file and parse mode
- **THEN** the diagnostics panel can call `POST /api/document-ingestions`
- **AND** displays the returned `ingest_id`, `status`, and `artifact_id`.

#### Scenario: Display structured ingestion errors
- **WHEN** ingestion submission fails
- **THEN** the diagnostics panel displays the backend error code and message.

### Requirement: External document VLM capability registration

The backend SHALL support registering `document.vlm.parse` as an HTTP capability when an external VLM provider is configured.

#### Scenario: VLM capability appears in registry
- **GIVEN** VLM provider integration is enabled
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the registry includes `document.vlm.parse`
- **AND** the capability uses `kind=vlm` and `transport=http`.

### Requirement: Document VLM parse normalization

The backend SHALL map VLM parse requests to the external provider and normalize responses into a provider-neutral semantic envelope.

#### Scenario: VLM invocation returns semantic understanding and evidence
- **WHEN** a client invokes `POST /api/capabilities/document.vlm.parse/invoke`
- **THEN** the response includes `summary`, `sections`, `entities`, `answers`, `evidence`, `warnings`, and `raw`.

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

### Requirement: External document layout capability registration

The backend SHALL support registering `document.layout.parse` as an HTTP capability when an external layout provider is configured.

#### Scenario: Layout capability is discoverable
- **GIVEN** layout provider integration is enabled
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the registry includes `document.layout.parse`
- **AND** the capability uses `kind=layout` and `transport=http`.

### Requirement: Document layout parse normalization

The backend SHALL map layout parse requests to the external provider and normalize responses into a provider-neutral envelope.

#### Scenario: Layout invocation returns markdown and table evidence
- **WHEN** a client invokes `POST /api/capabilities/document.layout.parse/invoke`
- **THEN** the response includes `markdown`, `elements`, `tables`, `pages`, `artifacts`, `warnings`, and `raw`.

### Requirement: Layout parse error code contract

The backend SHALL return stable error codes for layout parse input and provider failures.

#### Scenario: Unsupported layout media type is rejected
- **WHEN** `media_type` is not in `{application/pdf, image/png, image/jpeg}`
- **THEN** response `error.code` MUST be `LAYOUT_UNSUPPORTED_MEDIA_TYPE`.

#### Scenario: Invalid layout output format is rejected
- **WHEN** `output_format` is not `markdown` or `json`
- **THEN** response `error.code` MUST be `LAYOUT_INVALID_OUTPUT_FORMAT`.

#### Scenario: Missing layout input is rejected
- **WHEN** `file_base64` is missing or empty
- **THEN** response `error.code` MUST be `LAYOUT_INVALID_INPUT`.

#### Scenario: Layout provider failures are mapped
- **WHEN** provider returns non-zero/non-null `errorCode` or transport errors
- **THEN** response `error.code` SHOULD be `PADDLE_LAYOUT_PROVIDER_ERROR` for mapped provider failures.

#### Scenario: Unreachable layout provider is reported
- **WHEN** HTTP transport is unreachable
- **THEN** response `error.code` SHOULD be `CAPABILITY_PROVIDER_UNREACHABLE`.

### Requirement: Layout parse status visibility

The contract SHALL expose health and heartbeat states as documented in `unified-capability-runtime`:

#### Scenario: Layout provider status is visible
- **WHEN** a client inspects the layout capability
- **THEN** the status MUST be one of `ready`, `disabled`, `unconfigured`, `missing_dependency`, or `unreachable`.

### Requirement: Coze migration workflows may be exposed as provider-neutral capabilities
The capability runtime SHALL be able to expose ready Coze migration workflows as provider-neutral capabilities using stable capability ids.

#### Scenario: Ready workflow appears as capability
- **GIVEN** a Coze workflow `customer_intake` is active and ready
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the registry may include `coze.workflow.customer_intake`
- **AND** the capability contract includes `kind = workflow`
- **AND** the capability contract includes workflow identity, input schema, output schema, status, and governance metadata

#### Scenario: Draft workflow is not exposed as default callable capability
- **GIVEN** a Coze workflow status is `draft`
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the capability runtime MUST NOT expose it as a default callable production capability
- **AND** development visibility may remain available through the Coze migration registry

### Requirement: Coze workflow capability invocation must use standard envelopes
The capability runtime SHALL invoke Coze workflow capabilities through the same provider-neutral invoke envelope used by other capabilities.

#### Scenario: Invoke ready Coze workflow capability
- **WHEN** a client posts to `POST /api/capabilities/coze.workflow.customer_intake/invoke`
- **THEN** the backend validates the request against the workflow input schema
- **AND** returns a provider-neutral response envelope
- **AND** includes workflow run identity and structured result or error

#### Scenario: Blocked Coze workflow capability returns structured error
- **GIVEN** a workflow has unresolved readiness blockers
- **WHEN** a client invokes its capability id
- **THEN** the backend returns `ok = false`
- **AND** the error code is stable and machine-readable

