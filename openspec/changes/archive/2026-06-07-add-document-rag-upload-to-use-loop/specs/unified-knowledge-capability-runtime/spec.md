# unified-knowledge-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: Document RAG upload-to-use trial does not promote default knowledge runtime
The unified knowledge capability runtime SHALL treat document RAG upload-to-use results as explicit local trial evidence only.

#### Scenario: Upload-to-use loop succeeds
- **WHEN** the document RAG upload-to-use loop returns `go`
- **THEN** MyPrivateAgent may use the generated source id for explicit local RAG trial questions
- **AND** the success does not enable default `/api/chat` retrieval injection, source-to-agent binding, answer generation policy, or GraphRAG execution
