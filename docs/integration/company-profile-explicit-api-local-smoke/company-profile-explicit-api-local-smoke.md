# Company Profile Explicit API Local Smoke

- Contract: `company-profile-explicit-api-local-smoke-v1`
- Decision: `go`
- Reason: `company_profile_explicit_api_ready`
- Next Action: `use_explicit_api_for_local_business_trials`
- Endpoint: `/api/domain-agents/company_profile/live-grounded-answer`
- Agent: `company_profile`
- Domain: `company.profile`
- Provider: `http://127.0.0.1:8020`
- Generated At: `2026-06-12T07:31:26.272319+00:00`

## Result

| Metric | Value |
|---|---|
| `http_status_code` | `200` |
| `ok` | `True` |
| `api_status` | `go` |
| `document_count` | `2` |
| `citations` | `["company_profile_2025_trial#chunk-127", "company_profile_2025_trial#chunk-203"]` |

## Answer Preview

基于 company_profile_2025_trial#chunk-127, company_profile_2025_trial#chunk-203，已为 `company.profile` 生成受控回答预览：公司主营业务是什么？

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

## Blockers

None.

## Warnings

None.
