# unified-voice-runtime Specification

## Purpose
Defines the legacy local voice runtime contract for ASR/TTS compatibility while the recommended voice execution path is the external `unifiedTTSandASR` provider exposed through capability runtime. Vosk and Edge-TTS dependencies remain optional fallback dependencies and are not part of the default main backend.
## Requirements
### Requirement: Voice Runtime Capabilities
The backend SHALL expose a stable legacy voice capability contract for compatibility while recommending external voice provider execution through capability runtime.

#### Scenario: Runtime disabled by default
- **GIVEN** no voice runtime enablement environment variable is set
- **WHEN** a client requests `GET /api/voice/capabilities`
- **THEN** the response reports `enabled=false`
- **AND** it includes ASR and TTS provider names, modes, and unavailable status
- **AND** it does not require optional voice dependencies to be installed
- **AND** it identifies `/api/voice/*` as a legacy local compatibility surface.

#### Scenario: Runtime enabled with optional providers
- **GIVEN** `ENABLE_VOICE_RUNTIME=true`
- **WHEN** a client requests `GET /api/voice/capabilities`
- **THEN** the response reports the configured ASR and TTS provider names
- **AND** marks providers as `ready` only when their optional runtime dependencies/configuration are available.

#### Scenario: External voice provider is the recommended path
- **WHEN** a deployment needs ASR or TTS for normal development or production
- **THEN** it should enable `ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true`
- **AND** use `/api/capabilities/voice.tts.edge/*` and `/api/capabilities/voice.asr.vosk/*` as the primary MyPrivateAgent integration surface.

### Requirement: Text-to-Speech API
The backend SHALL expose a stable TTS endpoint backed by optional provider adapters.

#### Scenario: TTS provider unavailable
- **GIVEN** the voice runtime is disabled or the Edge-TTS dependency is not installed
- **WHEN** a client posts to `POST /api/voice/tts`
- **THEN** the backend returns a structured unavailable error
- **AND** server startup remains healthy.

#### Scenario: TTS provider ready
- **GIVEN** the voice runtime is enabled and Edge-TTS is available
- **WHEN** a client posts text, voice, rate, volume, and pitch options to `POST /api/voice/tts`
- **THEN** the backend returns audio bytes with an audio media type
- **AND** does not change `/api/chat`.

### Requirement: Speech-to-Text API
The backend SHALL expose a stable ASR endpoint backed by optional provider adapters.

#### Scenario: ASR provider unavailable
- **GIVEN** the voice runtime is disabled or the configured Vosk service/dependency is unavailable
- **WHEN** a client posts audio to `POST /api/voice/asr`
- **THEN** the backend returns a structured unavailable error
- **AND** server startup remains healthy.

#### Scenario: ASR streaming endpoint unavailable
- **GIVEN** the voice runtime is disabled or Vosk streaming is unavailable
- **WHEN** a client opens `WS /api/voice/asr/ws`
- **THEN** the server sends a structured unavailable message and closes the WebSocket cleanly.

#### Scenario: ASR streaming endpoint proxies PCM chunks
- **GIVEN** the voice runtime is enabled and the configured Vosk WebSocket server is ready
- **WHEN** a client sends binary PCM audio chunks to `WS /api/voice/asr/ws`
- **THEN** the backend forwards the chunks to Vosk
- **AND** returns provider-neutral JSON messages containing `provider`, `language`, `text`, `partial`, and `raw`.

### Requirement: Frontend Voice API Wrapper
The frontend SHALL provide a unified API wrapper for voice runtime calls.

#### Scenario: Frontend checks capabilities
- **WHEN** the frontend calls `voiceApi.getCapabilities()`
- **THEN** it requests `GET /voice/capabilities` through the existing API base and auth interceptor.

#### Scenario: Frontend requests TTS or ASR
- **WHEN** the frontend calls `voiceApi.synthesizeSpeech(...)` or `voiceApi.transcribeAudio(...)`
- **THEN** it uses the unified backend endpoints without changing chat message dispatch.
