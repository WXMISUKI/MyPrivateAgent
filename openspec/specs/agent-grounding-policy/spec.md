# agent-grounding-policy Specification

## Purpose

Define the caller-owned grounding policy contract and side-effect-free decision gate that controls whether external knowledge evidence may be used by a domain-agent answer path. This capability does not enable default `/api/chat` retrieval injection.

## Requirements

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

#### Scenario: Promotion gate consumes grounding decision
- **WHEN** a grounded-answer promotion gate evaluates a domain agent
- **THEN** it consumes the side-effect-free grounding policy decision as readiness evidence
- **AND** it does not enable retrieval, prompt injection, memory injection, or answer generation by itself

### Requirement: Grounding policy uses bounded control values
The system SHALL normalize grounding control fields into bounded values suitable for tests, Runtime Surface, and future promotion gates.

#### Scenario: Fallback policy is normalized
- **WHEN** a manifest declares `fallback_policy`
- **THEN** the normalized policy preserves a supported value such as `answer_without_claiming_sources`, `clarify`, `refuse`, or `refuse_or_clarify_when_no_evidence`

#### Scenario: Source ACL mode is normalized
- **WHEN** a manifest declares `source_acl_mode`
- **THEN** the normalized policy preserves a supported value such as `agent_manifest`, `provider_catalog`, or `intersection`

### Requirement: Grounding decision gate is side-effect-free
The system SHALL expose a deterministic grounding policy decision gate that does not invoke retrieval or mutate chat behavior.

#### Scenario: Default chat remains disabled
- **WHEN** no domain-agent grounding decision is requested
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** no provider retrieval, prompt injection, memory injection, or context packing behavior changes

#### Scenario: Agent policy is missing
- **WHEN** a grounding decision is requested for an unknown agent or an agent without declared grounding policy
- **THEN** the decision is `blocked` or `review`
- **AND** the output includes a machine-readable reason code

#### Scenario: Trial surface evaluates grounding decision
- **WHEN** the grounded-answer trial surface receives a caller-supplied evidence pack
- **THEN** it may evaluate the grounding decision for that evidence pack
- **AND** this does not invoke retrieval, mutate chat state, or compose an answer

### Requirement: Grounding decisions enforce cited evidence requirements
The grounding policy decision gate SHALL only allow grounded answer paths when policy and evidence requirements are satisfied.

#### Scenario: Cited evidence is answerable
- **WHEN** an agent policy requires citations
- **AND** the provided evidence pack has `status=answerable` and non-empty `allowed_citations`
- **THEN** the decision is `allowed`
- **AND** the allowed citations are returned as the citation allowlist

#### Scenario: Evidence is insufficient
- **WHEN** an agent policy requires citations or the requested domain is in `must_use_knowledge_for_domains`
- **AND** the provided evidence pack has `status=insufficient_evidence`
- **THEN** the decision is `blocked`
- **AND** the output recommends the configured fallback policy

#### Scenario: Citations are missing
- **WHEN** an agent policy requires citations
- **AND** the evidence pack has no allowed citations
- **THEN** the decision is `blocked`
- **AND** the output says citations are required

### Requirement: Graph grounding remains separately gated
The grounding policy decision gate SHALL NOT treat document RAG readiness as GraphRAG execution readiness.

#### Scenario: Graph evidence is requested before promotion
- **WHEN** a grounding decision requests graph usage
- **THEN** the decision is `blocked`
- **AND** the output identifies GraphRAG execution as not promoted
