# Local Knowledge Provider Corpus Trial

- Report: `local-knowledge-provider-corpus-trial-v1`
- Decision: `go`
- Reason: `local_corpus_trial_accepted`
- Provider Base URL: `http://127.0.0.1:8020`
- Source ID: `company_profile_2025_trial`
- API Key Configured: `False`
- Generated At: `2026-06-07T11:08:05.817039+00:00`

## Summary

| Metric | Value |
|---|---|
| `case_count` | `5` |
| `ready_case_count` | `5` |
| `review_case_count` | `0` |
| `blocked_case_count` | `0` |
| `invalid_citation_count` | `0` |
| `source_binding_status` | `not_created` |
| `default_chat_retrieval_injection` | `not_enabled` |
| `graph_execution_status` | `not_executed` |
| `runtime_promotion_status` | `unchanged` |

## Cases

| Case | Expected | Status | Reason | Retrieve | Answer | Citations | Invalid |
|---|---|---|---|---|---|---|---|
| `business_scope` | `answerable` | `ready` | `answerable_case_passed` | `3` | `answered` | `3` | `0` |
| `qualifications` | `answerable` | `ready` | `answerable_case_passed` | `3` | `answered` | `3` | `0` |
| `organization` | `answerable` | `ready` | `answerable_case_passed` | `3` | `answered` | `3` | `0` |
| `project_scale` | `answerable` | `ready` | `answerable_case_passed` | `3` | `answered` | `3` | `0` |
| `negative_refund_policy` | `insufficient_evidence` | `ready` | `negative_control_passed` | `0` | `insufficient_evidence` | `0` | `0` |

## Recommended Actions

- use_company_profile_source_for_explicit_myprivateagent_domain_trial
- keep_source_to_agent_binding_in_caller_control_plane
- do_not_enable_default_chat_retrieval_without_grounding_promotion

## Non-Goals

- does_not_start_provider_service
- does_not_create_source_to_agent_binding
- does_not_mutate_domain_agent_manifest
- does_not_write_audit_or_memory_records
- does_not_enable_default_chat_retrieval_injection
- does_not_run_myprivateagent_orchestration
- does_not_promote_retrieval_backend
- does_not_start_ocr_services
- does_not_execute_graphrag
