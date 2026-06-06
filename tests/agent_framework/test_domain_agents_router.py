import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.domain_agents import router


class DomainAgentsRouterTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
