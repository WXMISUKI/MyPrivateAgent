## MODIFIED Requirements

### Requirement: Recovery audit summary MUST consume retry evidence

Recovery audit summary MUST expose retry distribution from compact recovery operation evidence without requiring consumers to scan raw history.

#### Scenario: Retry status distribution is summarized

- **WHEN** recovery operation history contains retry evidence
- **THEN** `recovery_audit_summary.retry_status_counts` MUST count retry statuses
- **AND** it MUST expose the latest retry status
- **AND** it MUST expose the latest retry terminal reason when the latest retry evidence is terminal

#### Scenario: SDK-gate retry attempt evidence is summarized

- **WHEN** SDK recovery gates record retry attempt evidence inside recovery operation history
- **THEN** recovery audit summary MUST summarize that evidence exactly like helper-built operation evidence
- **AND** consumers MUST NOT need to scan SDK events or raw metadata to infer retry status

#### Scenario: No retry evidence is present

- **WHEN** recovery operation history contains no retry evidence
- **THEN** `recovery_audit_summary.retry_status_counts` MUST be empty
- **AND** latest retry fields MUST remain empty rather than inferred from operation status alone

