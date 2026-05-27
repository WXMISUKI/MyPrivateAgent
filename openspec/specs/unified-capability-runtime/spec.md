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

