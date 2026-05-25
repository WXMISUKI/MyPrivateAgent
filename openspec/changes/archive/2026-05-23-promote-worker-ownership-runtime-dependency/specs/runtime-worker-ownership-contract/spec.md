# runtime-worker-ownership-contract Specification Delta

## MODIFIED Requirements

### Requirement: Runtime MUST expose worker ownership as a first-class contract

The runtime MUST define a machine-readable worker ownership contract for any recovery or continuation operation that may run outside the original process. The default embedded runtime factory MUST expose the configured ownership adapter as a runtime dependency boundary.

#### Scenario: Ownership contract is declared

- **WHEN** a consumer inspects runtime recovery capabilities
- **THEN** the runtime MUST expose whether worker ownership is implemented
- **AND** it MUST expose the ownership contract version
- **AND** it MUST distinguish ownership readiness from durable storage readiness
- **AND** it MUST expose whether the default worker ownership adapter is durable
- **AND** it MUST identify that SDK enforcement remains opt-in on descriptor ownership evidence

#### Scenario: Runtime factory creates SDK with ownership dependency

- **WHEN** `EmbeddedRuntimeFactory.create_sdk()` is called without overriding ownership dependencies
- **THEN** the SDK MUST receive the factory's configured worker ownership store
- **AND** recovery gate behavior MUST remain descriptor-evidence driven
