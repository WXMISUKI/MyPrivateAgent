## ADDED Requirements

### Requirement: Knowledge provider supports domain-agent live trial retrieval
MyPrivateAgent SHALL be able to use the external knowledge provider RAG retrieve contract as an explicit domain-agent trial input.

#### Scenario: Domain-agent live trial retrieves provider evidence
- **WHEN** a domain-agent live grounded-answer trial calls `POST /api/rag/retrieve`
- **THEN** the provider result is interpreted through the existing `documents` and `metadata.evidence_pack` contract
- **AND** the retrieved evidence is treated as trial evidence, not as default chat context injection
