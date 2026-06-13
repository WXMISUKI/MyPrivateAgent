# knowledge-provider-caller-loop-closure Specification

## Purpose
TBD - created by archiving change close-knowledge-provider-caller-loop. Update Purpose after archive.
## Requirements
### Requirement: MyPrivateAgent documents local knowledge provider enablement
MyPrivateAgent SHALL document the local enablement sequence for consuming `unifiedKnowledgeRAG` through provider-neutral capability contracts.

#### Scenario: Runbook lists provider startup and health checks
- **WHEN** a maintainer opens the caller-loop runbook
- **THEN** it identifies the expected provider base URL and the provider-side health/preflight checks that should pass before MyPrivateAgent verification

#### Scenario: Runbook lists MyPrivateAgent environment settings
- **WHEN** a maintainer opens the caller-loop runbook
- **THEN** it lists `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true` and `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020`
- **AND** it does not instruct maintainers to store provider API keys in generated artifacts

#### Scenario: Runbook preserves runtime boundaries
- **WHEN** the runbook describes successful provider use
- **THEN** it states that default `/api/chat` retrieval injection, source binding automation, GraphRAG execution, and final answer policy remain outside this closure

### Requirement: Caller loop refreshes explicit provider-backed evidence
MyPrivateAgent SHALL refresh explicit caller-side artifacts that prove the external knowledge provider can be used without changing default runtime behavior.

#### Scenario: Explicit API local smoke passes
- **WHEN** `company_profile_explicit_api_local_smoke` runs against a reachable provider
- **THEN** the exported artifact records `decision=go`, HTTP 200, document count, citations, provider URL, and boundary fields showing no chat/model/tool/memory/audit mutation

#### Scenario: Provider feedback input is exportable
- **WHEN** the unified knowledge provider trial outcome is exported
- **THEN** the artifact includes `provider_feedback_input` with provider retrieve status, citation allowlist, blockers, warnings, provider base URL, agent id, and query

#### Scenario: Caller evidence remains explicit
- **WHEN** caller-loop evidence is refreshed
- **THEN** it does not mutate provider data, create source-to-agent bindings, enable default chat grounding, execute GraphRAG, or change provider runtime promotion state

### Requirement: Caller loop exposes focused verification commands
MyPrivateAgent SHALL provide a narrow verification path for this closure using existing scripts and focused tests.

#### Scenario: Verification covers capability provider registration
- **WHEN** focused backend tests run
- **THEN** they verify that the knowledge capability provider is absent by default and present when enabled by configuration

#### Scenario: Verification covers explicit live trial path
- **WHEN** focused backend tests or smoke commands run
- **THEN** they verify the explicit domain-agent provider-backed trial path without requiring frontend build or default chat execution

#### Scenario: Verification keeps active OpenSpec state clean
- **WHEN** the closure is archived
- **THEN** active OpenSpec changes are empty unless another real task is intentionally open

