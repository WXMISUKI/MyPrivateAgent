# Local RAG Question Trial Entrypoint

- Report: `local-rag-question-trial-entrypoint-v1`
- Decision: `go`
- Reason: `rag_question_answered`
- Provider Base URL: `http://127.0.0.1:8020`
- Source ID: `company_profile_2025_trial`
- Question: `公司有哪些资质或能力？`
- Answer Status: `answered`
- Evidence Status: `n/a`
- Generated At: `2026-06-08T01:34:34.945843+00:00`

## Answer

[company_profile_2025_trial#chunk-115] 理专项资质、市政公用工程监理乙级、公路工程综合乙级试验检测资质；公司通过
[company_profile_2025_trial#chunk-1] <!-- artifact_id: company_profile_2025_trial_ocr_document_upload source_id: company_profile_2025_trial parser_id: myprivateagent-ocr-artifact-handoff-v1 original_file: D:\xwechat_files\wxid_pc6sc451nt9022_dea0\msg\file\2026-06\公司简介2025年10月27日(1).pdf -->
[company_profile_2025_trial#chunk-3] 江苏交通工程咨询监理有限公司

## Citations

- `company_profile_2025_trial#chunk-115`
- `company_profile_2025_trial#chunk-1`
- `company_profile_2025_trial#chunk-3`

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
