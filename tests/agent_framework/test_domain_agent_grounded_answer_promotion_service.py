import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.services.domain_agent_grounded_answer_promotion_service import (
    DomainAgentGroundedAnswerPromotionService,
    build_domain_agent_grounded_answer_promotion_decision,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


class DomainAgentGroundedAnswerPromotionServiceTests(unittest.TestCase):
    def test_go_when_all_readiness_evidence_is_ready(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "trial_passed"},
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "go")
        self.assertEqual(decision["reason_code"], "grounded_answer_trial_ready")
        self.assertEqual(decision["blockers"], [])
        self.assertEqual(decision["warnings"], [])
        self.assertEqual(decision["boundary"]["default_chat_retrieval_injection"], "disabled")
        self.assertFalse(decision["boundary"]["runtime_behavior_changed"])

    def test_go_when_provider_governance_readiness_reports_rag_ready(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence=self._provider_governance_readiness(),
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "go")
        self.assertEqual(decision["evidence_summary"]["provider"]["reason_code"], "provider_rag_ready")
        self.assertEqual(decision["evidence_summary"]["provider"]["readiness_source"], "governance_readiness")
        self.assertEqual(decision["evidence_summary"]["provider"]["default_chat_grounding_status"], "gated")

    def test_blocks_when_provider_governance_readiness_is_unreachable(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence=self._provider_governance_readiness(overall_status="unreachable", rag_status="unreachable"),
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "blocked")
        self.assertIn(
            {"component": "provider", "status": "unreachable", "reason_code": "provider_unreachable"},
            decision["blockers"],
        )

    def test_reviews_when_provider_governance_readiness_has_degraded_catalog(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence=self._provider_governance_readiness(overall_status="degraded", source_catalog_status="degraded"),
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "review")
        self.assertIn(
            {"component": "provider", "status": "review", "reason_code": "provider_source_catalog_degraded"},
            decision["warnings"],
        )

    def test_blocks_graph_request_when_provider_graph_query_is_gated(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            graph_requested=True,
            provider_evidence=self._provider_governance_readiness(),
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "blocked")
        self.assertIn(
            {"component": "graph", "status": "blocked", "reason_code": "graphrag_not_promoted_by_provider_readiness"},
            decision["blockers"],
        )

    def test_blocks_when_provider_is_not_ready(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "degraded"},
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "blocked")
        self.assertIn(
            {"component": "provider", "status": "degraded", "reason_code": "provider_not_ready"},
            decision["blockers"],
        )

    def test_reviews_when_grounding_policy_is_missing(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service(include_policy=False))

        decision = service.evaluate(
            agent_id="ecommerce_support",
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["citation-1"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "review")
        self.assertIn(
            {"component": "grounding", "status": "review", "reason_code": "grounding_policy_not_declared"},
            decision["warnings"],
        )

    def test_blocks_when_required_citations_are_missing(self):
        service = DomainAgentGroundedAnswerPromotionService(self._registry_service())

        decision = service.evaluate(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": []},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(decision["decision"], "blocked")
        self.assertIn(
            {"component": "grounding", "status": "blocked", "reason_code": "citations_required"},
            decision["blockers"],
        )

    def test_blocks_graph_trial_until_graphrag_is_promoted(self):
        decision = build_domain_agent_grounded_answer_promotion_decision(
            agent_id="ecommerce_support",
            graph_requested=True,
            provider_evidence={"status": "ready"},
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
            registry_service=self._registry_service(),
        )

        self.assertEqual(decision["decision"], "blocked")
        self.assertIn(
            {"component": "graph", "status": "blocked", "reason_code": "graphrag_not_promoted"},
            decision["blockers"],
        )
        self.assertIn(
            {"component": "grounding", "status": "blocked", "reason_code": "graphrag_not_promoted"},
            decision["blockers"],
        )

    def _registry_service(self, *, include_policy=True):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        agent_dir = root / "ecommerce_support"
        agent_dir.mkdir()
        policy_block = (
            """
            grounding_policy:
              require_citations: true
              allow_ungrounded: false
              must_use_knowledge_for_domains:
                - refund.policy
              fallback_policy: refuse_or_clarify_when_no_evidence
              source_acl_mode: agent_manifest
            """
            if include_policy
            else ""
        )
        manifest = (
            """
            id: ecommerce_support
            name: Ecommerce Support
            version: 0.1.0
            roles:
              - id: default
                default: true
            capabilities:
              rag_sources:
                - refund_policy_docs
            """
            + policy_block
        )
        (agent_dir / "agent.yaml").write_text(
            textwrap.dedent(manifest).strip(),
            encoding="utf-8",
        )
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
