## ADDED Requirements

### Requirement: Agent manifests declare grounding policy
The system SHALL support a machine-readable grounding policy for domain agents without requiring an external knowledge provider to be ready.

#### Scenario: Agent declares explicit grounding policy
- **WHEN** a domain agent manifest includes `grounding_policy`
- **THEN** the normalized agent contract includes `grounding_policy`
- **AND** the policy includes `require_citations`, `allow_ungrounded`, `must_use_knowledge_for_domains`, `fallback_policy`, and `source_acl_mode` when declared

#### Scenario: Agent uses legacy retrieval policy fields
- **WHEN** a domain agent manifest includes `retrieval` but not `grounding_policy`
- **THEN** the normalized agent contract maps supported retrieval fields into `grounding_policy`
- **AND** the original knowledge source declarations remain unchanged

### Requirement: Grounding policy readiness is visible before enforcement
The system SHALL expose grounding policy readiness as governance-visible data before it changes default chat behavior.

#### Scenario: Runtime Surface reads grounding policy
- **WHEN** the Runtime Surface profile is assembled
- **THEN** domain-agent grounding policy data is visible to governance consumers
- **AND** the output indicates that default `/api/chat` retrieval injection is not enabled by this change

#### Scenario: Provider readiness is unavailable
- **WHEN** a policy references knowledge behavior and the external provider is absent or degraded
- **THEN** grounding readiness reports a machine-readable `unknown` or `degraded` state
- **AND** application startup and default chat behavior remain healthy

### Requirement: Grounding policy uses bounded control values
The system SHALL normalize grounding control fields into bounded values suitable for tests, Runtime Surface, and future promotion gates.

#### Scenario: Fallback policy is normalized
- **WHEN** a manifest declares `fallback_policy`
- **THEN** the normalized policy preserves a supported value such as `answer_without_claiming_sources`, `clarify`, `refuse`, or `refuse_or_clarify_when_no_evidence`

#### Scenario: Source ACL mode is normalized
- **WHEN** a manifest declares `source_acl_mode`
- **THEN** the normalized policy preserves a supported value such as `agent_manifest`, `provider_catalog`, or `intersection`
