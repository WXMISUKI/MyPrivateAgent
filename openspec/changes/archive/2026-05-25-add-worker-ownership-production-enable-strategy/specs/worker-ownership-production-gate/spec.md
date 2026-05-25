## MODIFIED Requirements

### Requirement: Worker ownership production gate MUST be machine-readable

The runtime MUST expose a production gate before worker ownership can become default execution authority for recovery, retry, or worker dispatch.

#### Scenario: Default enablement strategy is blocked

- **WHEN** any required production section is blocked or explicit default enablement is not requested
- **THEN** the production gate remains blocked
- **AND** `production_default_enabled` remains false
- **AND** the `fail_closed_default_decision` section evidence MUST identify blocking sections and explicit enablement state
