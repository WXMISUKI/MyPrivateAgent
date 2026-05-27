## 1. Knowledge Capability Contracts

- [x] 1.1 Add external knowledge provider configuration and HTTP capability definitions for RAG retrieve and graph query.
- [x] 1.2 Add focused backend tests for configured, unconfigured, and unreachable knowledge provider behavior.

## 2. Knowledge Registries

- [x] 2.1 Add read-only RAG source and knowledge graph registry contracts derived from domain agent manifests.
- [x] 2.2 Add focused backend tests proving `rag_sources` and `graph_sources` enter Runtime Surface without blocking empty registries.

## 3. Documentation

- [x] 3.1 Add `docs/guides/external_rag_provider_development.md` with external provider development rules and API contracts.
- [x] 3.2 Update domain agent and capability docs to reference Knowledge Provider, RAG sources, and graph source registration.

## 4. Validation

- [x] 4.1 Run focused backend tests for capability runtime and knowledge registries.
- [x] 4.2 Run `cmd /c openspec validate unified-knowledge-capability-runtime --strict` and `cmd /c openspec validate --specs --strict`.
