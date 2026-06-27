## ADDED Requirements

### Requirement: Coze Node Dependency Mapping
The system SHALL represent migrated Coze node dependencies as a machine-readable mapping.

#### Scenario: Coze nodes map to local capabilities
- **WHEN** a workflow manifest or source export declares Coze nodes such as HTTP, OCR, VLM, RAG, spreadsheet parsing, file reading, or model invocation
- **THEN** the dependency mapping identifies the target MyPrivateAgent capability, provider, tool, artifact flow, or unsupported blocker for each node type.

#### Scenario: Unsupported node is explicit
- **WHEN** a Coze node has no supported local capability or provider mapping
- **THEN** the dependency mapping reports `status = blocked`
- **AND** includes the missing capability or provider requirement.

### Requirement: Runtime Capability Readiness Mapping
The system SHALL map manifest runtime capabilities to current runtime support and provider readiness.

#### Scenario: Supported capability is ready
- **WHEN** a workflow declares a runtime capability that is supported and ready
- **THEN** the dependency mapping reports it as ready
- **AND** links it to the owning runtime or provider contract when available.

#### Scenario: Missing capability is blocked
- **WHEN** a workflow declares an unsupported runtime capability such as an unknown OCR, HTTP, RAG, or VLM capability
- **THEN** the workflow readiness includes a machine-readable blocker
- **AND** invoke remains fail-closed.

### Requirement: File And Artifact Dependency Mapping
The system SHALL distinguish local test files from runtime artifact references.

#### Scenario: File workflow declares artifact expectation
- **WHEN** a workflow requires file upload, OCR, VLM, spreadsheet parsing, or document analysis
- **THEN** the dependency mapping identifies whether the input uses local fixture, uploaded file, artifact id, or provider-owned job reference
- **AND** external callers are not required to use local filesystem paths.

### Requirement: Provider Readiness Linkage
The system SHALL link workflow dependencies to existing provider management surfaces when providers are involved.

#### Scenario: Provider-backed dependency is visible
- **WHEN** a workflow depends on a provider-backed capability such as OCR, VLM, RAG, graph query, ASR, TTS, or model inference
- **THEN** dependency mapping includes provider id, capability id, readiness status, and onboarding path when available.

#### Scenario: Provider unreachable blocks promotion
- **WHEN** a required provider-backed capability is unreachable or unconfigured
- **THEN** workflow promotion remains blocked or in review
- **AND** the blocker references the provider readiness failure.
