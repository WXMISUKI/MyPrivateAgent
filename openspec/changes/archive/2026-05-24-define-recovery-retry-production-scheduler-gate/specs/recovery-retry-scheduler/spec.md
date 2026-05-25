## MODIFIED Requirements

### Requirement: Scheduler MUST be opt-in

Automatic retry execution MUST remain disabled unless an explicit runtime or caller configuration enables it.

Production automatic retry MUST additionally require a ready production scheduler gate before any background or default retry execution can run.

#### Scenario: Default runtime

- **WHEN** no retry scheduler is configured
- **THEN** retry evidence remains available
- **AND** no automatic retry execution occurs

#### Scenario: Explicitly enabled retry

- **WHEN** the scheduler is explicitly enabled for a retryable recovery operation
- **THEN** it MUST execute only the approved recovery entrypoint
- **AND** the resulting recovery operation MUST include compact retry attempt evidence

#### Scenario: Production gate is blocked

- **WHEN** automatic retry is requested but production scheduler gate is blocked
- **THEN** the scheduler MUST remain in explicit opt-in mode
- **AND** no background or default retry execution occurs
