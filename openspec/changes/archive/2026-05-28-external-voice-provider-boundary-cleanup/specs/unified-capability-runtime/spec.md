## MODIFIED Requirements

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
