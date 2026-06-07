# Local Knowledge Base User Loop

- Contract: `local-knowledge-base-user-loop-v1`
- Decision: `go`
- Reason: `local_knowledge_base_user_loop_ready`
- Next Action: `start_local_business_qa_trial_with_explicit_company_profile_entrypoint`
- Source: `company_profile_2025_trial`
- Provider: `http://127.0.0.1:8020`
- Generated At: `2026-06-07T09:52:04.072217+00:00`

## Entry Point

| Field | Value |
|---|---|
| `endpoint` | `/api/domain-agents/company_profile/live-grounded-answer` |
| `agent_id` | `company_profile` |
| `domain` | `company.profile` |
| `query` | `公司主营业务是什么？` |
| `http_status_code` | `200` |
| `api_status` | `go` |
| `document_count` | `3` |
| `answer_preview` | `基于 company_profile_2025_trial#chunk-1, company_profile_2025_trial#chunk-4, company_profile_2025_trial#chunk-5，已为 `company.profile` 生成受控回答预览：公司主营业务是什么？` |

## Suggested Questions

| Question | Expected Mode |
|---|---|
| 公司主营业务是什么？ | `answerable` |
| 公司有哪些资质？ | `answerable` |
| 公司组织机构包括哪些部门？ | `answerable` |
| 公司完成过哪些工程规模？ | `answerable` |
| 售后退款凭证规则 | `insufficient_evidence` |

## Citations

- Count: `3`
- Values: `["company_profile_2025_trial#chunk-1", "company_profile_2025_trial#chunk-4", "company_profile_2025_trial#chunk-5"]`

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

## Warnings

None.

## Blockers

None.
