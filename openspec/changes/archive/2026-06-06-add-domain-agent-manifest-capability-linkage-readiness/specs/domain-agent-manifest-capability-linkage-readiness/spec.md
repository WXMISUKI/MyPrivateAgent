## ADDED Requirements

### Requirement: Domain agent capability linkage is read-only
The system SHALL expose read-only linkage readiness for domain agent manifest-declared Tool, Skill, and MCP capabilities.

#### Scenario: Declared local capabilities resolve
- **WHEN** a domain agent declares tools, skills, and MCP references
- **AND** those references are present in the current ToolRuntime, SkillRuntime, and MCP runtime contracts
- **THEN** the linkage report has `status = ready`
- **AND** the report lists resolved tool, skill, and MCP references

#### Scenario: Declared local capability is missing
- **WHEN** a domain agent declares a tool, skill, or MCP reference that is not present in the current local contracts
- **THEN** the linkage report has `status = review`
- **AND** the report lists the missing reference under the matching capability family
- **AND** the report recommends reviewing the manifest or registering the missing capability

### Requirement: External knowledge sources remain outside local linkage enforcement
The linkage report SHALL preserve RAG and graph source declarations as external-provider references without checking or executing them in MyPrivateAgent.

#### Scenario: RAG or graph source is declared
- **WHEN** a domain agent declares `rag_sources` or `graph_sources`
- **THEN** the linkage report marks those families as `not_checked`
- **AND** the owner is reported as `external_provider`
- **AND** no provider call, retrieval call, source binding, or GraphRAG execution is performed

### Requirement: Catalog includes linkage readiness without changing runtime behavior
The domain agent catalog SHALL include capability linkage readiness without changing chat, prompt, memory, retrieval, or tool execution behavior.

#### Scenario: Catalog is read
- **WHEN** a caller requests `GET /api/agents`
- **THEN** each ready agent entry includes `capability_linkage`
- **AND** reading the catalog does not mutate manifests, registries, prompts, memory, retrieval, source bindings, tools, skills, or MCP sessions
