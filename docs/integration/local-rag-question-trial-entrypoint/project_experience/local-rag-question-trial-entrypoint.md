# Local RAG Question Trial Entrypoint

- Report: `local-rag-question-trial-entrypoint-v1`
- Decision: `go`
- Reason: `rag_question_answered`
- Provider Base URL: `http://127.0.0.1:8020`
- Source ID: `company_profile_2025_trial`
- Question: `公司有哪些项目经验或服务范围？`
- Answer Status: `answered`
- Evidence Status: `n/a`
- Generated At: `2026-06-08T01:34:35.052015+00:00`

## Answer

[company_profile_2025_trial#chunk-129] 咨询、技术服务，工程项目管理，建设工程的项目管理、技术咨询，市政公用工程
[company_profile_2025_trial#chunk-151] 理念，持续发扬“守法公正、诚信履约、科学管理、创新服务”的公司精神，以诚
[company_profile_2025_trial#chunk-155] “今天的业主是我们永远的业主”为服务宗旨，践行“用诚信和实力塑造公司品牌”

## Citations

- `company_profile_2025_trial#chunk-129`
- `company_profile_2025_trial#chunk-151`
- `company_profile_2025_trial#chunk-155`

## Summary

| Metric | Value |
|---|---|
| `final_decision` | `go` |
| `answer_status` | `answered` |
| `retrieved_document_count` | `3` |
| `citation_count` | `3` |
| `invalid_citation_count` | `0` |
| `evidence_status` | `None` |
| `source_binding_status` | `not_created` |
| `default_chat_retrieval_injection` | `not_enabled` |
| `memory_write_status` | `not_written` |
| `audit_write_status` | `not_written` |
| `service_start_status` | `not_started` |
| `graph_execution_status` | `not_executed` |

## Recommended Actions

- use_this_source_id_for_explicit_local_business_rag_trial

## Non-Goals

- does_not_enable_default_chat_retrieval_injection
- does_not_create_source_to_agent_binding
- does_not_mutate_domain_agent_manifests
- does_not_write_memory_audit_approval_or_governance_records
- does_not_start_external_services
- does_not_execute_graphrag
