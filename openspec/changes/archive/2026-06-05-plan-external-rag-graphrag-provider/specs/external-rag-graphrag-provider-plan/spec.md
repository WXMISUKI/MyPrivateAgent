## ADDED Requirements

### Requirement: External provider implementation plan is documented
The repository SHALL document the implementation plan for an independent RAG / GraphRAG provider that remains outside the MyPrivateAgent core backend.

#### Scenario: Developer reads the provider plan
- **WHEN** a developer opens the external provider planning guide
- **THEN** the guide describes provider responsibilities, MyPrivateAgent responsibilities, framework recommendations, project layout, HTTP contracts, source catalog, lifecycle boundaries, and verification steps

### Requirement: Framework choices are explicit
The provider plan SHALL define LlamaIndex as the preferred document RAG orchestration reference and Neo4j GraphRAG as the preferred graph retrieval reference.

#### Scenario: Developer chooses a retrieval implementation
- **WHEN** a knowledge source is document-heavy and citation-oriented
- **THEN** the plan recommends a LlamaIndex-backed RAG pipeline
- **AND** it keeps LlamaIndex dependencies inside the external provider

#### Scenario: Developer chooses graph retrieval
- **WHEN** a knowledge source requires entities, relations, paths, ontology constraints, or graph traversal
- **THEN** the plan recommends a Neo4j GraphRAG-backed graph pipeline
- **AND** it keeps Neo4j and graph dependencies inside the external provider

### Requirement: Provider source catalog is defined
The provider plan SHALL require a provider-managed source catalog for knowledge bases and graph namespaces.

#### Scenario: Provider reports source readiness
- **WHEN** MyPrivateAgent or an operator checks provider capabilities
- **THEN** the provider exposes source ids, graph ids, readiness status, version metadata, and machine-readable degraded reasons

### Requirement: Knowledge results remain evidence-first
The provider plan SHALL require RAG retrieval and graph query results to return compact model context plus auditable evidence.

#### Scenario: RAG result is returned
- **WHEN** a RAG retrieval request succeeds
- **THEN** the response includes short answer context
- **AND** each document includes stable citation evidence

#### Scenario: Graph result is returned
- **WHEN** a graph query succeeds
- **THEN** the response includes graph id, entities, relations, paths, and evidence

### Requirement: Implementation cadence follows spec to archive
The planning docs SHALL define a cadence from OpenSpec proposal, to implementation, to verification, to archive.

#### Scenario: Team starts the provider work
- **WHEN** the team begins implementation
- **THEN** tasks are executed from the OpenSpec change
- **AND** verification evidence is recorded before archive
