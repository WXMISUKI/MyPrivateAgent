## ADDED Requirements

### Requirement: Recovery audit summary MUST consume retry evidence
Recovery audit summary MUST expose retry distribution from compact recovery operation evidence without requiring consumers to scan raw history.

#### Scenario: Retry status distribution is summarized
- **WHEN** recovery operation history contains retry evidence
- **THEN** `recovery_audit_summary.retry_status_counts` MUST count retry statuses
- **AND** it MUST expose the latest retry status
- **AND** it MUST expose the latest retry terminal reason when the latest retry evidence is terminal

#### Scenario: No retry evidence is present
- **WHEN** recovery operation history contains no retry evidence
- **THEN** `recovery_audit_summary.retry_status_counts` MUST be empty
- **AND** latest retry fields MUST remain empty rather than inferred from operation status alone

