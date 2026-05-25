## ADDED Requirements

### Requirement: Runtime worker ownership renewal supervisor MUST expose controlled lifecycle

The renewal supervisor MUST provide explicit lifecycle controls that are inactive by default and fail closed on renewal loss.

#### Scenario: Supervisor is inactive by default

- **WHEN** a renewal supervisor is constructed
- **THEN** `status()` MUST report inactive
- **AND** no thread, timer, worker, or renewal loop MUST start automatically

#### Scenario: Explicit start performs controlled renewal

- **GIVEN** a worker owns a valid lease
- **WHEN** `start(...)` is called with matching ownership evidence
- **THEN** the supervisor MUST perform a renewal using the existing `renew_once(...)` path
- **AND** `status()` MUST expose active lifecycle evidence and latest renewal status

#### Scenario: Stop prevents further renewal loop work

- **GIVEN** a renewal supervisor has been explicitly started
- **WHEN** `stop()` is called
- **THEN** `status()` MUST report inactive
- **AND** the supervisor MUST NOT continue renewal loop work

#### Scenario: Start fails closed

- **WHEN** `start(...)` receives stale fencing, expired ownership, mismatched identity, or no store
- **THEN** the supervisor MUST remain inactive or blocked
- **AND** `status()` MUST preserve the latest blocked renewal reason
- **AND** no default production recovery authorization is granted
