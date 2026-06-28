## ADDED Requirements

### Requirement: Provider configuration read model SHALL expose masked provider settings
The system SHALL expose a read-only provider configuration list that includes provider identity, display name, configuration source, base URL, model name, and a masked API key when applicable.

#### Scenario: Known provider is listed with masked secrets
- **WHEN** a client reads the provider configuration list
- **THEN** the response SHALL include the known provider entries
- **AND THEN** each entry SHALL include `name`, `display_name`, `requires_api_key`, `configured`, `config_source`, `base_url`, `model_name`, and `api_key_masked` when the provider requires a key

#### Scenario: Non-secret provider omits masked key
- **WHEN** a provider does not require an API key
- **THEN** the configuration list SHALL omit raw secret values
- **AND THEN** `api_key_masked` SHALL be null or absent for that provider

### Requirement: Provider configuration updates SHALL be explicit and fail closed
The system SHALL allow explicit updates to provider configuration fields and SHALL reject unknown providers.

#### Scenario: Provider update persists overrides
- **WHEN** a client updates a known provider with a base URL, API key, or model name
- **THEN** the system SHALL persist the update as a local override
- **AND THEN** the subsequent effective configuration SHALL reflect the updated values

#### Scenario: Unknown provider update is blocked
- **WHEN** a client attempts to update an unknown provider
- **THEN** the system SHALL fail closed
- **AND THEN** the response SHALL indicate the provider is unknown

### Requirement: Provider connection testing SHALL be explicit and side-effect-free
The system SHALL provide an explicit provider test action that checks provider connectivity and authentication without exposing secrets or mutating unrelated runtime state.

#### Scenario: Ollama test returns model count
- **WHEN** a client tests a configured Ollama provider
- **THEN** the system SHALL attempt a connectivity check against the provider base URL
- **AND THEN** the response SHALL report success or failure without returning secret values

#### Scenario: Ark test validates key presence and reachability
- **WHEN** a client tests a configured Ark provider
- **THEN** the system SHALL require an API key to be present
- **AND THEN** the response SHALL report success, warning, or error based on connectivity and authentication status

#### Scenario: Unsupported provider test fails closed
- **WHEN** a client tests a provider family that the control plane does not support
- **THEN** the test action SHALL fail closed
- **AND THEN** the response SHALL identify the provider family as unsupported

### Requirement: Settings view SHALL consume provider configuration as a controlled surface
The system SHALL expose provider configuration in the Settings view as a controlled surface that allows review, editing, and testing without exposing raw secrets.

#### Scenario: Settings view renders provider configuration panel
- **WHEN** a user opens the model/provider section in Settings
- **THEN** the UI SHALL render provider configuration entries and their current status
- **AND THEN** the UI SHALL preserve secret masking in the displayed values

#### Scenario: Settings view can save provider changes
- **WHEN** a user edits provider base URL, API key, or model name from the panel
- **THEN** the UI SHALL submit the explicit update to the configuration API
- **AND THEN** the panel SHALL reflect the saved configuration source
