## MODIFIED Requirements

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
