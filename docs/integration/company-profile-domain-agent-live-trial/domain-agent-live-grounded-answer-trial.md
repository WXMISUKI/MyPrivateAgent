# Domain Agent Live Grounded Answer Trial

- Contract: `domain-agent-live-grounded-answer-trial-v1`
- Status: `go`
- Reason: `live_grounded_answer_trial_ready`
- Next Action: `proceed_with_explicit_grounded_answer_trial`
- Agent: `company_profile`
- Domain: `company.profile`
- Provider: `http://127.0.0.1:8020`
- Generated At: `2026-06-07T03:06:22.664480+00:00`

## Provider Retrieve

| Metric | Value |
|---|---|
| `status` | `ready` |
| `reason_code` | `provider_retrieve_ready` |
| `document_count` | `3` |
| `evidence_pack_status` | `answerable` |
| `citation_policy` | `use_only_returned_citations` |
| `allowed_citations` | `["company_profile_2025_trial#chunk-1", "company_profile_2025_trial#chunk-4", "company_profile_2025_trial#chunk-5"]` |

## Downstream Status

| Stage | Status | Reason |
|---|---|---|
| `trial` | `go` | `grounded_answer_trial_ready` |
| `package` | `ready` | `grounded_answer_package_ready` |
| `composition` | `ready` | `grounded_answer_composition_ready` |

## Boundary

| Boundary | Value |
|---|---|
| `default_chat_retrieval_injection` | `disabled` |
| `chat_invocation` | `not_performed` |
| `model_invocation` | `not_performed` |
| `tool_execution` | `not_performed` |
| `source_binding_creation` | `not_performed` |
| `memory_write` | `not_performed` |
| `audit_write` | `not_performed` |
| `trace_write` | `not_performed` |
| `graphrag_execution` | `not_promoted` |
| `runtime_behavior_changed` | `False` |
