import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.domain_agents import router


class DomainAgentsRouterTests(unittest.TestCase):
    def test_agents_catalog_endpoint_returns_catalog_contract(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.build_catalog.return_value = {
            "contract_version": "domain-agent-catalog-v1",
            "status": "ready",
            "total_agents": 1,
            "ready_agents": 1,
            "invalid_agents": 0,
            "agents": [
                {
                    "id": "ecommerce_support",
                    "name": "Ecommerce Support",
                    "capability_linkage": {"status": "ready"},
                }
            ],
            "errors": [],
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_catalog_service",
            return_value=fake_service,
        ):
            response = TestClient(app).get("/api/agents")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "domain-agent-catalog-v1")
        self.assertEqual(payload["agents"][0]["id"], "ecommerce_support")
        self.assertEqual(payload["agents"][0]["capability_linkage"]["status"], "ready")
        fake_service.build_catalog.assert_called_once()

    def test_grounded_answer_trial_endpoint_returns_trial_report(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.run_trial.return_value.to_dict.return_value = {
            "contract_version": "domain-agent-grounded-answer-trial-surface-v1",
            "agent_id": "ecommerce_support",
            "trial_status": "go",
            "reason_code": "grounded_answer_trial_ready",
            "recommended_next_action": "start_repo_side_grounded_answer_trial",
            "grounding_decision": {"decision": "allowed"},
            "promotion_decision": {"decision": "go"},
            "citation_allowlist": ["refund_policy_2026#section-3"],
            "blockers": [],
            "warnings": [],
            "boundary": {
                "default_chat_retrieval_injection": "disabled",
                "provider_invocation": "not_performed",
                "answer_generation": "not_performed",
                "runtime_behavior_changed": False,
            },
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_grounded_answer_trial_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/ecommerce_support/grounded-answer-trial",
                json={
                    "domain": "refund.policy",
                    "query": "退款政策是什么？",
                    "evidence_pack": {
                        "status": "answerable",
                        "allowed_citations": ["refund_policy_2026#section-3"],
                    },
                    "provider_evidence": {"status": "trial_passed"},
                    "promptops_evidence": {"prompt_key": "refund_policy", "version": "2", "status": "active"},
                    "memoryops_evidence": {"retrieved_knowledge_promotion_mode": "explicit_only"},
                    "eval_evidence": {"overall_status": "passed"},
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["trial"]["trial_status"], "go")
        fake_service.run_trial.assert_called_once()
        call_kwargs = fake_service.run_trial.call_args.kwargs
        self.assertEqual(call_kwargs["agent_id"], "ecommerce_support")
        self.assertEqual(call_kwargs["domain"], "refund.policy")
        self.assertFalse(call_kwargs["graph_requested"])

    def test_grounded_answer_trial_endpoint_marks_blocked_as_not_ok(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.run_trial.return_value.to_dict.return_value = {
            "trial_status": "blocked",
            "blockers": [{"component": "provider", "reason_code": "provider_not_ready"}],
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_grounded_answer_trial_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/ecommerce_support/grounded-answer-trial",
                json={"graph_requested": True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ok"])
        self.assertTrue(fake_service.run_trial.call_args.kwargs["graph_requested"])

    def test_grounded_answer_package_dry_run_endpoint_returns_package(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.build_package.return_value.to_dict.return_value = {
            "contract_version": "domain-agent-grounded-answer-package-dry-run-v1",
            "agent_id": "ecommerce_support",
            "package_status": "ready",
            "reason_code": "grounded_answer_package_ready",
            "allowed_citations": ["refund_policy_2026#section-3"],
            "evidence_items": [{"source_type": "citation", "citation": "refund_policy_2026#section-3"}],
            "prompt_binding": {"prompt_key": "refund_policy", "version": "2", "status": "active"},
            "memory_boundary": {"retrieved_knowledge_promotion_mode": "explicit_only"},
            "fallback_policy": "refuse_or_clarify_when_no_evidence",
            "blockers": [],
            "warnings": [],
            "boundary": {
                "provider_invocation": "not_performed",
                "model_invocation": "not_performed",
                "answer_generation": "not_performed",
            },
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_grounded_answer_package_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/ecommerce_support/grounded-answer-package-dry-run",
                json={
                    "domain": "refund.policy",
                    "query": "退款政策是什么？",
                    "trial_report": {"trial_status": "go"},
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["package"]["package_status"], "ready")
        call_kwargs = fake_service.build_package.call_args.kwargs
        self.assertEqual(call_kwargs["agent_id"], "ecommerce_support")
        self.assertEqual(call_kwargs["domain"], "refund.policy")

    def test_grounded_answer_package_dry_run_endpoint_marks_blocked_as_not_ok(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.build_package.return_value.to_dict.return_value = {
            "package_status": "blocked",
            "blockers": [{"component": "graph", "reason_code": "graphrag_not_promoted"}],
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_grounded_answer_package_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/ecommerce_support/grounded-answer-package-dry-run",
                json={"graph_requested": True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ok"])
        self.assertTrue(fake_service.build_package.call_args.kwargs["graph_requested"])

    def test_grounded_answer_composition_trial_endpoint_returns_preview(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.run_trial.return_value.to_dict.return_value = {
            "contract_version": "domain-agent-grounded-answer-composition-trial-v1",
            "agent_id": "ecommerce_support",
            "composition_status": "ready",
            "reason_code": "grounded_answer_composition_ready",
            "answer_preview": "基于 refund_policy_2026#section-3，已生成受控回答预览。",
            "used_citations": ["refund_policy_2026#section-3"],
            "composition_policy": {"mode": "deterministic_preview", "citation_mode": "allowlist_only"},
            "fallback_behavior": {"when_blocked": "refuse_or_clarify_when_no_evidence"},
            "blockers": [],
            "warnings": [],
            "boundary": {"model_invocation": "not_performed", "answer_generation": "not_performed"},
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_grounded_answer_composition_trial_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/ecommerce_support/grounded-answer-composition-trial",
                json={"package": {"package_status": "ready"}},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["composition"]["composition_status"], "ready")

    def test_grounded_answer_composition_trial_endpoint_marks_blocked_as_not_ok(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.run_trial.return_value.to_dict.return_value = {
            "composition_status": "blocked",
            "blockers": [{"component": "graph", "reason_code": "graphrag_not_promoted"}],
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_grounded_answer_composition_trial_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/ecommerce_support/grounded-answer-composition-trial",
                json={"graph_requested": True},
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ok"])

    def test_live_grounded_answer_endpoint_returns_compact_response(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.run.return_value = {
            "ok": True,
            "status": "go",
            "reason_code": "live_grounded_answer_trial_ready",
            "answer_preview": "基于 company_profile_2025_trial#chunk-4，已生成受控回答预览。",
            "citations": ["company_profile_2025_trial#chunk-4"],
            "documents": [{"source_id": "company_profile_2025_trial"}],
            "boundary": {"default_chat_retrieval_injection": "disabled"},
            "trial": {"provider_retrieve": {"knowledge_base_ids": ["company_profile_2025_trial"]}},
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_live_grounded_answer_api_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/company_profile/live-grounded-answer",
                json={
                    "domain": "company.profile",
                    "query": "公司主营业务是什么？",
                    "provider_base_url": "http://127.0.0.1:8020",
                    "top_k": 3,
                    "timeout_seconds": 5,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["citations"], ["company_profile_2025_trial#chunk-4"])
        call_kwargs = fake_service.run.call_args.kwargs
        self.assertEqual(call_kwargs["agent_id"], "company_profile")
        self.assertEqual(call_kwargs["domain"], "company.profile")
        self.assertEqual(call_kwargs["query"], "公司主营业务是什么？")
        self.assertEqual(call_kwargs["provider_base_url"], "http://127.0.0.1:8020")
        self.assertEqual(call_kwargs["top_k"], 3)
        self.assertEqual(call_kwargs["timeout_seconds"], 5.0)

    def test_live_grounded_answer_endpoint_does_not_echo_provider_api_key(self):
        app = FastAPI()
        app.include_router(router)
        fake_service = Mock()
        fake_service.run.return_value = {
            "ok": False,
            "status": "blocked",
            "reason_code": "provider_unreachable",
            "blockers": [{"component": "provider", "reason_code": "provider_unreachable"}],
            "boundary": {"default_chat_retrieval_injection": "disabled"},
            "trial": {},
        }

        with patch(
            "backend.routers.domain_agents.get_domain_agent_live_grounded_answer_api_service",
            return_value=fake_service,
        ):
            response = TestClient(app).post(
                "/api/domain-agents/company_profile/live-grounded-answer",
                json={
                    "query": "公司主营业务是什么？",
                    "provider_api_key": "secret-provider-key",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("secret-provider-key", response.text)
        self.assertEqual(fake_service.run.call_args.kwargs["provider_api_key"], "secret-provider-key")


if __name__ == "__main__":
    unittest.main()
