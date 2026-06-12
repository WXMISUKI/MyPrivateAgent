# Unified Knowledge Provider Trial Outcome

- Report: `unified-knowledge-provider-repo-side-trial-v1`
- Status: `trial_passed`
- Decision: `proceed_with_myprivateagent_integration_hardening`
- Provider Base URL: `http://127.0.0.1:8020`
- Agent ID: `company_profile`
- API Key Configured: `False`
- Generated At: `2026-06-12T07:31:24.265028+00:00`

## Summary

| Metric | Value |
|---|---|
| `total_checks` | `5` |
| `ready_checks` | `5` |
| `review_checks` | `0` |
| `blocked_checks` | `0` |
| `ready_check_ids` | `["provider_health", "provider_manifest", "provider_preflight", "source_bindings", "rag_retrieve"]` |
| `review_check_ids` | `[]` |
| `blocked_check_ids` | `[]` |
| `agent_id` | `company_profile` |
| `query` | `refund policy` |
| `provider_document_rag_readiness` | `{"supplied": false, "status": "not_supplied", "recommended_action": "supply_phase24_provider_readiness_artifact_for_document_rag_trial_context"}` |
| `source_binding_policy_owner` | `caller` |
| `runtime_promotion_status` | `unchanged` |

## Checks

| Check | Endpoint | Status | Recommended Action | Summary |
|---|---|---|---|---|
| `provider_health` | `/health` | `ready` | `no_action_required` | `{"provider_status": "ok", "service": "unifiedKnowledgeProvider"}` |
| `provider_manifest` | `/api/provider/manifest` | `ready` | `no_action_required` | `{"provider_id": "unifiedKnowledgeProvider", "contract_version": "knowledge-provider-contract-v1", "capability_count": 5}` |
| `provider_preflight` | `/api/provider/preflight` | `ready` | `no_action_required` | `{"bindable": true, "status": null, "required_capability_count": 0}` |
| `source_bindings` | `/api/provider/source-bindings` | `ready` | `no_action_required` | `{"status": "ready", "source_count": 6, "bindable_source_count": 6, "selected_source_ids": ["refund_policy_docs", "logistics_faq", "split_refund_policy_docs"], "source_binding_policy_owner": "caller"}` |
| `rag_retrieve` | `/api/rag/retrieve` | `ready` | `no_action_required` | `{"document_count": 2, "knowledge_base_ids": ["refund_policy_docs", "logistics_faq", "split_refund_policy_docs"], "evidence_pack_version": "evidence-pack-v1", "evidence_pack_status": "answerable", "citation_policy": "use_only_returned_citations", "allowed_citations": ["refund_policy_2026#exact-refund-code", "split_refund_policy_2026#form-code"], "allowed_citation_count": 2}` |

## Provider Feedback Input

| Field | Value |
|---|---|
| `live_trial_status` | `go` |
| `reason_code` | `repo_side_trial_passed` |
| `provider_base_url` | `http://127.0.0.1:8020` |
| `agent_id` | `company_profile` |
| `query` | `refund policy` |
| `provider_retrieve` | `{"status": "ready", "reason_code": "provider_retrieve_ready", "document_count": 2, "evidence_pack_status": "answerable", "citation_policy": "use_only_returned_citations", "allowed_citations": ["refund_policy_2026#exact-refund-code", "split_refund_policy_2026#form-code"], "blockers": [], "warnings": [], "evidence_pack": {"status": "answerable", "citation_policy": "use_only_returned_citations", "allowed_citations": ["refund_policy_2026#exact-refund-code", "split_refund_policy_2026#form-code"]}}` |
| `blockers` | `[]` |
| `warnings` | `[]` |

## Notes

- This outcome is a read-only MyPrivateAgent repo-side trial over the external knowledge provider contract.
- The trial does not create source-to-agent binding, approvals, audit records, runtime promotions, or final answer policy.
- Provider API key values are never written to this artifact.
- The provider_feedback_input payload is caller-owned and can be passed into unifiedKnowledgeRAG Phase 25 feedback without manual field reconstruction.
