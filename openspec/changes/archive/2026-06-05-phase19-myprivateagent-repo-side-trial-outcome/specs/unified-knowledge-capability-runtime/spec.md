## ADDED Requirements

### Requirement: Unified knowledge provider repo-side trial outcome is exportable
MyPrivateAgent SHALL provide a read-only repo-side trial outcome for the unified knowledge provider integration.

#### Scenario: Trial checks minimal provider access path
- **WHEN** the repo-side trial outcome is generated
- **THEN** it checks provider health, manifest discovery, preflight readiness, RAG retrieve consumption, and source binding review access
- **AND** it records each check with status, endpoint, summary, and recommended action

#### Scenario: Trial emits caller-owned decision
- **WHEN** all required trial checks pass
- **THEN** the outcome status is `trial_passed`
- **AND** the recommended next action is to proceed with MyPrivateAgent integration hardening

#### Scenario: Trial fails closed on required protocol failures
- **WHEN** the provider is unreachable, returns invalid JSON, fails a required endpoint, or omits required response fields
- **THEN** the outcome status is `trial_blocked`
- **AND** the output identifies the failing check and recovery action

### Requirement: Repo-side trial preserves provider and caller boundaries
The repo-side trial SHALL remain a read-only caller-side smoke and not mutate provider or caller control-plane state.

#### Scenario: Trial does not create source binding
- **WHEN** source binding review is checked
- **THEN** the trial only reads provider source-binding evidence
- **AND** it does not create source-to-agent binding, approvals, audit records, or runtime policy decisions

#### Scenario: Trial does not change runtime defaults
- **WHEN** the trial outcome is generated
- **THEN** it does not change chat defaults, retrieval backend defaults, GraphRAG execution, or answer composition behavior
- **AND** it does not store provider API key values in generated artifacts
