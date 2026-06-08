# Local RAG Question Trial Entrypoint

- Report: `local-rag-question-trial-entrypoint-v1`
- Decision: `go`
- Reason: `rag_question_answered`
- Provider Base URL: `http://127.0.0.1:8020`
- Source ID: `company_profile_2025_trial`
- Question: `公司组织结构或部门有哪些？`
- Answer Status: `answered`
- Evidence Status: `n/a`
- Generated At: `2026-06-08T01:34:35.002429+00:00`

## Answer

[company_profile_2025_trial#chunk-663] 根据贵组织的申请，本公司依据《环境管理体系要求及使
[company_profile_2025_trial#chunk-787] 根据贵组织的申请，本公司依据（职业健康安全管理体系
[company_profile_2025_trial#chunk-921] 根据贵组织的中请，本公司依据《质量管理体系要求》

## Citations

- `company_profile_2025_trial#chunk-663`
- `company_profile_2025_trial#chunk-787`
- `company_profile_2025_trial#chunk-921`

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
