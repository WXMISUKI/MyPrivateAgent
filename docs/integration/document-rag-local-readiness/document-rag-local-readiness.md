# Document RAG Local Readiness

- Report: `document-rag-local-readiness-v1`
- Decision: `go`
- Reason: `document_rag_local_readiness_ready`
- Generated At: `2026-06-07T12:23:12.663173+00:00`
- OCR Provider: `http://127.0.0.1:8080`
- OCR Profile: `gpu`
- OCR Timeout Seconds: `180.0`
- Knowledge Provider: `http://127.0.0.1:8020`
- Source ID: `company_profile_2025_trial`
- Provider Repo: `D:\AI\AIcode\unifiedKnowledgeRAG`

## Checks

| Check | Status | Reason | Endpoint | Summary |
|---|---|---|---|---|
| `ocr_provider` | `ready` | `ocr_profile_ready` | `http://127.0.0.1:8080/health` | `{"large_pdf_timeout_recommendation_seconds": 120.0, "ocr_profile": "gpu", "ocr_timeout_seconds": 180.0, "raw": {"errorCode": 0, "errorMsg": "Healthy", "logId": "a153c9e0-c706-451c-8167-eec4ed1a1175"}, "status": "ready"}` |
| `knowledge_provider` | `ready` | `knowledge_provider_health_ready` | `http://127.0.0.1:8020/health` | `{"raw": {"answer": {"backend": "deterministic", "backend_status": "ready", "index_status": null, "reason": null, "status": "ready"}, "graph": {"backend": null, "backend_status": null, "index_status": null, "reason": "Graph query execution is not in slice v1.", "status": "planned"}, "rag": {"backend": "fixture", "backend_status": "ready", "index_status": "ready", "reason": null, "status": "ready"}, "service": "unifiedKnowledgeProvider", "status": "ok"}, "status": "ready"}` |
| `knowledge_source_catalog` | `ready` | `source_visible` | `http://127.0.0.1:8020/api/rag/sources` | `{"source_id": "company_profile_2025_trial", "visible_source_ids": ["company_profile_2025_trial", "logistics_faq", "refund_policy_docs"]}` |
| `provider_ingestion_command` | `ready` | `provider_python_command_ready` | `D:\AI\AIcode\unifiedKnowledgeRAG\scripts\export_parser_artifact_local_ingestion_loop.py` | `{"command": ["conda", "run", "-n", "GRAPHRAG", "python", "--version"], "provider_python": "conda run -n GRAPHRAG python", "provider_repo_path": "D:\\AI\\AIcode\\unifiedKnowledgeRAG", "return_code": 0, "stderr": "", "stdout": "Python 3.11.15"}` |
| `runtime_boundaries` | `ready` | `side_effect_free_readiness_only` | `n/a` | `{"default_chat_retrieval_injection": "not_enabled", "document_parse_status": "not_run", "graph_execution_status": "not_executed", "memory_audit_governance_write_status": "not_written", "provider_ingestion_status": "not_run", "service_start_status": "not_started", "source_binding_status": "not_created"}` |

## Summary

| Metric | Value |
|---|---|
| `final_decision` | `go` |
| `ready_check_count` | `5` |
| `review_check_count` | `0` |
| `blocked_check_count` | `0` |
| `ocr_profile` | `gpu` |
| `ocr_timeout_seconds` | `180.0` |
| `large_pdf_timeout_recommendation_seconds` | `120.0` |
| `default_chat_retrieval_injection` | `not_enabled` |
| `source_binding_status` | `not_created` |
| `document_parse_status` | `not_run` |
| `provider_ingestion_status` | `not_run` |
| `service_start_status` | `not_started` |
| `graph_execution_status` | `not_executed` |

## Recommended Actions

- run_document_rag_upload_to_use_loop_for_real_document
- use_gpu_ocr_service_endpoint_for_large_pdf_trials

## Non-Goals

- does_not_upload_parse_or_ingest_documents
- does_not_start_external_services
- does_not_enable_default_chat_retrieval_injection
- does_not_create_source_to_agent_binding
- does_not_write_memory_audit_approval_or_governance_records
- does_not_execute_graphrag
- does_not_add_frontend_document_management_ui
