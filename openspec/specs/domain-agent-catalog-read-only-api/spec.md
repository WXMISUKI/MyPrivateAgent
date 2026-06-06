# domain-agent-catalog-read-only-api Specification

## Purpose
Define the read-only API-facing domain agent catalog that wraps the manifest-driven registry in a narrower caller-consumable contract.

## Requirements
### Requirement: Domain agent catalog is exposed as a read-only API
The system SHALL expose a read-only domain agent catalog API that wraps the manifest-driven domain agent registry in an API-facing contract.

#### Scenario: Ready catalog is listed
- **WHEN** a caller requests `GET /api/agents`
- **AND** the domain agent registry has ready agents
- **THEN** the response includes `contract_version = domain-agent-catalog-v1`
- **AND** the response includes ready agent entries with identity, roles, declared capabilities, capability counts, and grounding summaries

#### Scenario: Empty catalog stays stable
- **WHEN** a caller requests `GET /api/agents`
- **AND** no domain agent manifests exist
- **THEN** the response returns `status = empty`
- **AND** `agents = []`
- **AND** `errors = []`

### Requirement: Catalog preserves diagnostics without widening runtime behavior
The catalog SHALL preserve invalid-manifest diagnostics and SHALL NOT change chat or runtime behavior.

#### Scenario: Invalid manifest is present
- **WHEN** the wrapped domain agent registry is degraded by an invalid manifest
- **THEN** the catalog returns `status = degraded`
- **AND** the response includes compact error entries for invalid manifests

#### Scenario: Catalog is read
- **WHEN** a caller reads the catalog
- **THEN** no manifest is mutated
- **AND** no tool, skill, MCP, prompt, memory, or retrieval behavior is activated or changed
