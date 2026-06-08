# Local RAG Question Trial Entrypoint

- Report: `local-rag-question-trial-entrypoint-v1`
- Decision: `go`
- Reason: `rag_question_insufficient_evidence`
- Provider Base URL: `http://127.0.0.1:8020`
- Source ID: `company_profile_2025_trial`
- Question: `售后退款凭证规则是什么？`
- Answer Status: `insufficient_evidence`
- Evidence Status: `n/a`
- Generated At: `2026-06-08T01:34:35.120839+00:00`

## Answer

(empty)

## Citations

- n/a

## Summary

| Metric | Value |
|---|---|
| `final_decision` | `go` |
| `answer_status` | `insufficient_evidence` |
| `retrieved_document_count` | `0` |
| `citation_count` | `0` |
| `invalid_citation_count` | `0` |
| `evidence_status` | `None` |
| `source_binding_status` | `not_created` |
| `default_chat_retrieval_injection` | `not_enabled` |
| `memory_write_status` | `not_written` |
| `audit_write_status` | `not_written` |
| `service_start_status` | `not_started` |
| `graph_execution_status` | `not_executed` |

## Recommended Actions

- adjust_question_or_ingest_more_relevant_local_documents

## Non-Goals

- does_not_enable_default_chat_retrieval_injection
- does_not_create_source_to_agent_binding
- does_not_mutate_domain_agent_manifests
- does_not_write_memory_audit_approval_or_governance_records
- does_not_start_external_services
- does_not_execute_graphrag
