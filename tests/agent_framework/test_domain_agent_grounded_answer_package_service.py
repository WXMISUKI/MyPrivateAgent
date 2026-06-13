import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.services.domain_agent_grounded_answer_package_service import (
    DomainAgentGroundedAnswerPackageService,
    build_grounded_answer_package_dry_run,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


class DomainAgentGroundedAnswerPackageServiceTests(unittest.TestCase):
    def test_package_ready_when_trial_is_go(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            query="退款政策是什么？",
            provider_evidence={"status": "trial_passed"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "ready")
        self.assertEqual(package["reason_code"], "grounded_answer_package_ready")
        self.assertEqual(package["allowed_citations"], ["refund_policy_2026#section-3"])
        self.assertEqual(package["evidence_items"][0]["source_type"], "citation")
        self.assertEqual(package["prompt_binding"]["prompt_key"], "refund_policy")
        self.assertEqual(package["memory_boundary"]["retrieved_knowledge_promotion_mode"], "explicit_only")
        self.assertEqual(package["boundary"]["model_invocation"], "not_performed")
        self.assertEqual(package["boundary"]["answer_generation"], "not_performed")

    def test_package_preserves_ready_provider_readiness(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            query="退款政策是什么？",
            provider_evidence=self._provider_governance_readiness(),
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "ready")
        self.assertEqual(package["provider_readiness"]["status"], "ready")
        self.assertTrue(package["provider_readiness"]["ready"])
        self.assertEqual(package["provider_readiness"]["reason_code"], "provider_rag_ready")
        self.assertEqual(package["provider_readiness"]["rag_retrieve_status"], "ready")
        self.assertEqual(package["provider_readiness"]["source_catalog_status"], "ready")
        self.assertEqual(package["provider_readiness"]["graph_query_status"], "gated")
        self.assertEqual(package["provider_readiness"]["default_chat_grounding_status"], "gated")
        self.assertEqual(package["provider_readiness"]["promotion_boundary"]["provider_invocation"], "not_performed")
        self.assertEqual(package["boundary"]["provider_invocation"], "not_performed")
        self.assertEqual(package["boundary"]["chat_invocation"], "not_performed")

    def test_package_review_preserves_degraded_provider_catalog_warning(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence=self._provider_governance_readiness(
                overall_status="degraded",
                source_catalog_status="degraded",
            ),
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "review")
        self.assertEqual(package["provider_readiness"]["status"], "review")
        self.assertFalse(package["provider_readiness"]["ready"])
        self.assertEqual(package["provider_readiness"]["source_catalog_status"], "degraded")
        self.assertIn(
            {"component": "provider", "status": "review", "reason_code": "provider_source_catalog_degraded"},
            package["provider_readiness"]["warnings"],
        )

    def test_package_blocked_preserves_unreachable_provider_blocker(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence=self._provider_governance_readiness(
                overall_status="unreachable",
                rag_status="unreachable",
            ),
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "blocked")
        self.assertEqual(package["provider_readiness"]["status"], "unreachable")
        self.assertFalse(package["provider_readiness"]["ready"])
        self.assertIn(
            {"component": "provider", "status": "unreachable", "reason_code": "provider_unreachable"},
            package["provider_readiness"]["blockers"],
        )

    def test_package_blocked_preserves_provider_graph_gated_boundary(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            graph_requested=True,
            provider_evidence=self._provider_governance_readiness(graph_status="gated"),
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "blocked")
        self.assertEqual(package["provider_readiness"]["graph_query_status"], "gated")
        self.assertEqual(package["provider_readiness"]["promotion_boundary"]["graphrag_execution"], "not_promoted")
        self.assertIn(
            {"component": "graph", "status": "blocked", "reason_code": "graphrag_not_promoted_by_provider_readiness"},
            package["provider_readiness"]["blockers"],
        )

    def test_package_review_when_trial_reviews(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "review")
        self.assertTrue(package["warnings"])

    def test_package_blocked_when_trial_blocked(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "degraded"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(package["package_status"], "blocked")
        self.assertIn(
            {"component": "provider", "status": "degraded", "reason_code": "provider_not_ready"},
            package["blockers"],
        )

    def test_package_blocks_when_graph_requested(self):
        package = build_grounded_answer_package_dry_run(
            agent_id="ecommerce_support",
            graph_requested=True,
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
            registry_service=self._registry_service(),
        )

        self.assertEqual(package["package_status"], "blocked")
        self.assertIn(
            {"component": "graph", "status": "blocked", "reason_code": "graphrag_not_promoted"},
            package["blockers"],
        )

    def test_package_can_consume_prebuilt_trial_report(self):
        service = DomainAgentGroundedAnswerPackageService(registry_service=self._registry_service())

        package = service.build_package(
            agent_id="ecommerce_support",
            trial_report={
                "agent_id": "ecommerce_support",
                "trial_status": "go",
                "reason_code": "grounded_answer_trial_ready",
                "citation_allowlist": ["refund_policy_2026#section-3"],
                "grounding_decision": {"fallback_policy": "refuse_or_clarify_when_no_evidence"},
                "blockers": [],
                "warnings": [],
                "request_summary": {"domain": "refund.policy", "query": "退款政策是什么？"},
                "evidence_summary": {
                    "promptops": {"prompt_key": "refund_policy", "version": "2", "status": "active"},
                    "memoryops": {"retrieved_knowledge_promotion_mode": "explicit_only"},
                },
            },
        ).to_dict()

        self.assertEqual(package["package_status"], "ready")
        self.assertEqual(package["query"], "退款政策是什么？")
        self.assertEqual(package["domain"], "refund.policy")
        self.assertEqual(package["fallback_policy"], "refuse_or_clarify_when_no_evidence")
        self.assertEqual(package["provider_readiness"], {})

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

    def _provider_governance_readiness(
        self,
        *,
        overall_status="ready",
        rag_status="ready",
        source_catalog_status="ready",
        graph_status="gated",
    ):
        return {
            "governance_readiness": {
                "overall_status": overall_status,
                "rag_retrieve": {"status": rag_status},
                "source_catalog": {"status": source_catalog_status},
                "graph_query": {"status": graph_status},
                "default_chat_grounding": {"status": "gated"},
            }
        }


if __name__ == "__main__":
    unittest.main()
