# unified-capability-runtime Specification

## ADDED Requirements

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
