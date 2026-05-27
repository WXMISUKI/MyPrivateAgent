# voice-input-web-speech Specification

## Purpose
TBD - created by archiving change voice-input-web-speech. Update Purpose after archive.
## Requirements
### Requirement: Chat input exposes browser-side voice input
The chat input SHALL expose a microphone control when the browser supports `SpeechRecognition` or `webkitSpeechRecognition`.

#### Scenario: Supported browser starts recognition
- **GIVEN** the browser exposes a Speech Recognition constructor
- **WHEN** the user clicks the microphone control
- **THEN** the control starts recognition
- **AND** the recognition instance uses `lang = zh-CN`
- **AND** it sets `continuous = true`
- **AND** it sets `interimResults = true`

### Requirement: Recognition updates the existing text input
Voice recognition SHALL update the existing chat textarea without changing the chat send API.

#### Scenario: Interim and final transcripts appear in textarea
- **GIVEN** the user has typed existing text
- **AND** voice recognition is active
- **WHEN** an interim transcript event is received
- **THEN** the textarea includes the existing text and interim transcript
- **WHEN** a final transcript event is received
- **THEN** the textarea keeps the final transcript for sending through the existing chat flow

### Requirement: Voice input can be stopped and fails quietly
The chat input SHALL allow stopping active recognition and SHALL degrade quietly when speech recognition is unavailable.

#### Scenario: User stops active recognition
- **GIVEN** recognition is active
- **WHEN** the user clicks the microphone control again
- **THEN** recognition is stopped
- **AND** the listening state is cleared

#### Scenario: Unsupported browser
- **GIVEN** the browser does not expose Speech Recognition
- **WHEN** the chat input renders
- **THEN** the microphone control is disabled
- **AND** normal manual typing and sending remain available

