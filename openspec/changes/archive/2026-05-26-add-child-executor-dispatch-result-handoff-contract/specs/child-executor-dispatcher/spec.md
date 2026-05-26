## ADDED Requirements

### Requirement: Dispatcher MUST attach dispatch result handoff evidence
The child executor dispatcher MUST attach compact result handoff evidence to dispatcher attempts after backend invocation or fail-closed blocking.

#### Scenario: Dispatcher invokes sandbox backend
- **WHEN** the dispatcher invokes a ready sandbox backend adapter
- **THEN** the returned dispatch attempt MUST include `dispatch_result_handoff`
- **AND** the evidence MUST identify whether output and audit references are present
- **AND** it MUST NOT claim parent merge or retry scheduling occurred

#### Scenario: Dispatcher blocks before backend invocation
- **WHEN** the dispatcher blocks due to disabled dispatcher, blocked contract, missing adapter, unsafe payload, adapter exception, or malformed backend result
- **THEN** the returned dispatch attempt MUST include blocked result handoff evidence
- **AND** the evidence MUST preserve the blocked reason in compact form
