## ADDED Requirements

### Requirement: Domain agent manifests document retrieval policy
Domain agent manifests SHALL support documented knowledge retrieval policy for agents that bind RAG or graph sources.

#### Scenario: Agent declares retrieval policy
- **GIVEN** a domain agent manifest declares `capabilities.rag_sources` or `capabilities.graph_sources`
- **WHEN** a developer inspects the manifest
- **THEN** the manifest can include a `retrieval` section describing mode, citation requirement, fallback policy, and default retrieval limits

### Requirement: Domain agent prompt assets separate role from provider data
Domain agent assets SHALL keep role behavior and retrieval behavior in domain-agent prompts or policy files, not in the external provider source catalog.

#### Scenario: Agent defines knowledge behavior
- **GIVEN** a domain agent uses external RAG or graph sources
- **WHEN** its prompts are authored
- **THEN** prompts describe role boundaries, evidence usage, and fallback behavior
- **AND** provider source configuration remains limited to data, index, and retrieval metadata
