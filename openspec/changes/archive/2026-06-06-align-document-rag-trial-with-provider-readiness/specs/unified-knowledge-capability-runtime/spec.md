## ADDED Requirements

### Requirement: Repo-side document RAG trial records provider readiness closure
The unified knowledge provider repo-side trial outcome SHALL optionally consume provider-side document RAG trial readiness closure evidence as read-only context.

#### Scenario: Provider readiness closure supports trial start
- **WHEN** the trial outcome is generated with a provider readiness artifact path
- **AND** the artifact reports `decision=go`
- **AND** the artifact reports `trial_readiness_state=ready_for_repo_side_document_rag_trial`
- **THEN** the trial outcome includes a `provider_document_rag_readiness` check with status `ready`
- **AND** the trial still runs the live provider health, manifest, preflight, source-binding, and RAG retrieve checks

#### Scenario: Provider readiness closure is blocked
- **WHEN** the trial outcome is generated with a provider readiness artifact path
- **AND** the artifact is missing, invalid, malformed, or reports a blocked decision
- **THEN** the trial outcome includes a blocked `provider_document_rag_readiness` check
- **AND** the trial outcome identifies the recovery action before continuing integration

#### Scenario: Provider readiness closure is omitted
- **WHEN** the trial outcome is generated without a provider readiness artifact path
- **THEN** the trial outcome remains compatible with the existing HTTP-only repo-side trial
- **AND** the output records that provider document RAG readiness evidence was not supplied

### Requirement: Provider readiness cannot replace caller-side trial checks
Provider-side readiness evidence SHALL NOT bypass MyPrivateAgent repo-side trial checks or mutate caller/provider state.

#### Scenario: Provider readiness is ready
- **WHEN** provider document RAG readiness evidence is `ready`
- **THEN** the trial still requires live HTTP trial checks before emitting `trial_passed`
- **AND** the trial does not create source-to-agent binding, approval records, audit policy changes, runtime promotion, default chat retrieval injection, or GraphRAG execution
