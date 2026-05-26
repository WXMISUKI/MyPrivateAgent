## ADDED Requirements

### Requirement: Dispatch result handoff MUST preserve retry audit policy evidence
Dispatch result handoff MUST include nested retry audit policy evidence so consumers can distinguish retryable failures from actual retry scheduling.

#### Scenario: Result handoff includes retry audit policy
- **WHEN** result handoff is built from a dispatcher attempt
- **THEN** it MUST include `dispatch_result_retry_audit_policy`
- **AND** `retry_scheduled` MUST remain false
- **AND** parent merge and production dispatch authorization MUST remain false
