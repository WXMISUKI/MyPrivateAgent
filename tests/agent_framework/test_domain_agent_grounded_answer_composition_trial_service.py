import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.services.domain_agent_grounded_answer_composition_trial_service import (
    DomainAgentGroundedAnswerCompositionTrialService,
    build_grounded_answer_composition_trial,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


class DomainAgentGroundedAnswerCompositionTrialServiceTests(unittest.TestCase):
    def test_composition_ready_when_package_is_ready(self):
        service = DomainAgentGroundedAnswerCompositionTrialService(registry_service=self._registry_service())

        composition = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            query="退款政策是什么？",
            provider_evidence={"status": "trial_passed"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(composition["composition_status"], "ready")
        self.assertEqual(composition["reason_code"], "grounded_answer_composition_ready")
        self.assertEqual(composition["used_citations"], ["refund_policy_2026#section-3"])
        self.assertIn("refund_policy_2026#section-3", composition["answer_preview"])
        self.assertEqual(composition["composition_policy"]["citation_mode"], "allowlist_only")
        self.assertEqual(composition["boundary"]["model_invocation"], "not_performed")

    def test_composition_review_when_package_reviews(self):
        service = DomainAgentGroundedAnswerCompositionTrialService(registry_service=self._registry_service())

        composition = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(composition["composition_status"], "review")
        self.assertIsNone(composition["answer_preview"])
        self.assertTrue(composition["warnings"])

    def test_composition_blocked_when_package_blocked(self):
        service = DomainAgentGroundedAnswerCompositionTrialService(registry_service=self._registry_service())

        composition = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "degraded"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(composition["composition_status"], "blocked")
        self.assertIsNone(composition["answer_preview"])
        self.assertTrue(composition["blockers"])

    def test_composition_blocks_graph_request(self):
        composition = build_grounded_answer_composition_trial(
            agent_id="ecommerce_support",
            graph_requested=True,
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
            registry_service=self._registry_service(),
        )

        self.assertEqual(composition["composition_status"], "blocked")
        self.assertIn(
            {"component": "graph", "status": "blocked", "reason_code": "graphrag_not_promoted"},
            composition["blockers"],
        )

    def test_composition_can_consume_prebuilt_package(self):
        service = DomainAgentGroundedAnswerCompositionTrialService(registry_service=self._registry_service())

        composition = service.run_trial(
            agent_id="ecommerce_support",
            package={
                "agent_id": "ecommerce_support",
                "package_status": "ready",
                "reason_code": "grounded_answer_package_ready",
                "query": "退款政策是什么？",
                "domain": "refund.policy",
                "allowed_citations": ["refund_policy_2026#section-3"],
                "fallback_policy": "refuse_or_clarify_when_no_evidence",
                "blockers": [],
                "warnings": [],
            },
        ).to_dict()

        self.assertEqual(composition["composition_status"], "ready")
        self.assertEqual(composition["used_citations"], ["refund_policy_2026#section-3"])
        self.assertIn("退款政策是什么？", composition["answer_preview"])

    def _registry_service(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        agent_dir = root / "ecommerce_support"
        agent_dir.mkdir()
        manifest = """
            id: ecommerce_support
            name: Ecommerce Support
            version: 0.1.0
            roles:
              - id: default
                default: true
            capabilities:
              rag_sources:
                - refund_policy_docs
            grounding_policy:
              require_citations: true
              allow_ungrounded: false
              must_use_knowledge_for_domains:
                - refund.policy
              fallback_policy: refuse_or_clarify_when_no_evidence
              source_acl_mode: agent_manifest
        """
        (agent_dir / "agent.yaml").write_text(textwrap.dedent(manifest).strip(), encoding="utf-8")
        return DomainAgentRegistryService(root)


if __name__ == "__main__":
    unittest.main()
