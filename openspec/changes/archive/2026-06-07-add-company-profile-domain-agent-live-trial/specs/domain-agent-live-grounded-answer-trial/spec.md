## MODIFIED Requirements

### Requirement: Company profile live trial is manifest-scoped
The system SHALL support an explicit company-profile domain agent live grounded-answer trial using the manifest-declared `company_profile_2025_trial` RAG source.

#### Scenario: Company profile agent retrieves from the declared source
- **GIVEN** the `company_profile` domain agent manifest declares `capabilities.rag_sources: [company_profile_2025_trial]`
- **AND** the configured provider returns `documents` and `metadata.evidence_pack.status=answerable`
- **WHEN** the live trial runs for domain `company.profile`
- **THEN** the provider retrieve request uses `knowledge_base_ids=["company_profile_2025_trial"]`
- **AND** the trial report status is `go`
- **AND** the output includes provider retrieve summary, package dry-run, and grounded-answer composition trial output

#### Scenario: Company profile live trial remains explicit
- **WHEN** the company-profile live trial runs
- **THEN** it does not call `/api/chat`
- **AND** it does not create source-to-agent binding, write memory, write audit or trace records, execute tools, call GraphRAG, mutate provider state, start OCR, promote retrieval defaults, or enable default chat retrieval injection
