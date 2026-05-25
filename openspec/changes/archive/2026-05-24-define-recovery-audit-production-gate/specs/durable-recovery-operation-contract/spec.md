## MODIFIED Requirements

### Requirement: SDK MUST expose a recovery operation boundary

The Embedded SDK contract MUST declare the supported durable recovery operation entrypoints and the worker ownership boundary. Future worker ownership, retry, and audit hardening contracts MUST extend or consume this recovery operation evidence instead of replacing it with parallel recovery status models.

#### Scenario: Contract declares production audit readiness

- **WHEN** a consumer calls the recovery operation contract builder
- **THEN** the contract MUST include recovery audit production readiness evidence
- **AND** the evidence MUST declare operation history and audit summary support
- **AND** it MUST declare `authorization_source = false`
