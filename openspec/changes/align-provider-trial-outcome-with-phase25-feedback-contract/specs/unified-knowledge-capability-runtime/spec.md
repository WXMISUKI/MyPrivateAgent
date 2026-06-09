## ADDED Requirements

### Requirement: Repo-side trial outcome can feed provider-side feedback closure
MyPrivateAgent SHALL export a repo-side unified knowledge provider trial outcome that can be reused as input to provider-side feedback closure without manual field reconstruction.

#### Scenario: Trial outcome includes provider feedback contract fields
- **WHEN** the unified knowledge provider repo-side trial outcome is exported
- **THEN** the artifact includes the minimum caller-side fields needed by the provider Phase 25 feedback contract
- **AND** the output remains read-only and caller-owned

#### Scenario: Incomplete trial evidence stays conservative
- **WHEN** the repo-side trial outcome does not have enough evidence to prove a caller-side success state for provider follow-up
- **THEN** the feedback-compatible shape remains conservative
- **AND** it does not imply `no_provider_action_required` unless the required evidence is present
