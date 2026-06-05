import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.services.domain_agent_grounded_answer_trial_service import (
    DomainAgentGroundedAnswerTrialService,
    build_domain_agent_grounded_answer_trial_report,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


class DomainAgentGroundedAnswerTrialServiceTests(unittest.TestCase):
    def test_trial_go_when_grounding_and_promotion_are_ready(self):
        service = DomainAgentGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            query="退款政策是什么？",
            provider_evidence={"status": "trial_passed"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(report["trial_status"], "go")
        self.assertEqual(report["grounding_decision"]["decision"], "allowed")
        self.assertEqual(report["promotion_decision"]["decision"], "go")
        self.assertEqual(report["citation_allowlist"], ["refund_policy_2026#section-3"])
        self.assertEqual(report["boundary"]["provider_invocation"], "not_performed")
        self.assertEqual(report["boundary"]["chat_invocation"], "not_performed")
        self.assertFalse(report["boundary"]["runtime_behavior_changed"])

    def test_trial_reviews_when_promptops_evidence_is_missing(self):
        service = DomainAgentGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(report["trial_status"], "review")
        self.assertIn(
            {"component": "promptops", "status": "missing", "reason_code": "promptops_evidence_missing"},
            report["warnings"],
        )

    def test_trial_blocks_when_provider_is_degraded(self):
        service = DomainAgentGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "degraded"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(report["trial_status"], "blocked")
        self.assertIn(
            {"component": "provider", "status": "degraded", "reason_code": "provider_not_ready"},
            report["blockers"],
        )

    def test_trial_blocks_when_required_citations_are_missing(self):
        service = DomainAgentGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": []},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
        ).to_dict()

        self.assertEqual(report["trial_status"], "blocked")
        self.assertEqual(report["grounding_decision"]["reason_code"], "citations_required")

    def test_trial_blocks_graph_request_until_graphrag_is_promoted(self):
        report = build_domain_agent_grounded_answer_trial_report(
            agent_id="ecommerce_support",
            graph_requested=True,
            provider_evidence={"status": "ready"},
            evidence_pack={"status": "answerable", "allowed_citations": ["refund_policy_2026#section-3"]},
            promptops_evidence={"prompt_key": "refund_policy", "version": "2", "status": "active"},
            memoryops_evidence={"retrieved_knowledge_promotion_mode": "explicit_only"},
            eval_evidence={"overall_status": "passed"},
            registry_service=self._registry_service(),
        )

        self.assertEqual(report["trial_status"], "blocked")
        self.assertIn(
            {"component": "graph", "status": "blocked", "reason_code": "graphrag_not_promoted"},
            report["blockers"],
        )

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
