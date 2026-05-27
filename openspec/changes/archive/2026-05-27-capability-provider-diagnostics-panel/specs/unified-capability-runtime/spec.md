# unified-capability-runtime Specification

## ADDED Requirements

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
