import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.services.agent_grounding_policy_service import (
    AgentGroundingPolicyService,
    build_grounding_policy_decision,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


class AgentGroundingPolicyServiceTests(unittest.TestCase):
    def test_allows_answerable_evidence_with_required_citations(self):
        service = AgentGroundingPolicyService(self._registry_service())

        decision = service.decide(
            agent_id="ecommerce_support",
            domain="refund.policy",
            evidence_pack={
                "status": "answerable",
                "allowed_citations": ["refund_policy_2026#section-3"],
            },
        ).to_dict()

        self.assertEqual(decision["decision"], "allowed")
        self.assertEqual(decision["reason_code"], "answerable_evidence_pack")
        self.assertEqual(decision["citation_allowlist"], ["refund_policy_2026#section-3"])
        self.assertEqual(decision["boundary"]["default_chat_retrieval_injection"], "disabled")
        self.assertFalse(decision["boundary"]["runtime_behavior_changed"])

    def test_blocks_insufficient_evidence_for_required_domain(self):
        service = AgentGroundingPolicyService(self._registry_service())

        decision = service.decide(
            agent_id="ecommerce_support",
            domain="refund.policy",
            evidence_pack={"status": "insufficient_evidence", "allowed_citations": []},
        ).to_dict()

        self.assertEqual(decision["decision"], "blocked")
        self.assertEqual(decision["reason_code"], "insufficient_evidence")
        self.assertEqual(decision["recommended_action"], "refuse_or_clarify_when_no_evidence")

    def test_blocks_when_citations_are_required_but_missing(self):
        service = AgentGroundingPolicyService(self._registry_service())

        decision = service.decide(
            agent_id="ecommerce_support",
            domain="refund.policy",
            evidence_pack={"status": "answerable", "allowed_citations": []},
        ).to_dict()

        self.assertEqual(decision["decision"], "blocked")
        self.assertEqual(decision["reason_code"], "citations_required")

    def test_reviews_agent_without_grounding_policy(self):
        service = AgentGroundingPolicyService(self._registry_service(include_policy=False))

        decision = service.decide(
            agent_id="ecommerce_support",
            evidence_pack={"status": "answerable", "allowed_citations": ["citation-1"]},
        ).to_dict()

        self.assertEqual(decision["decision"], "review")
        self.assertEqual(decision["reason_code"], "grounding_policy_not_declared")

    def test_blocks_graph_request_until_graphrag_is_promoted(self):
        decision = build_grounding_policy_decision(
            agent_id="ecommerce_support",
            graph_requested=True,
            registry_service=self._registry_service(),
        )

        self.assertEqual(decision["decision"], "blocked")
        self.assertEqual(decision["reason_code"], "graphrag_not_promoted")
        self.assertEqual(decision["boundary"]["graphrag_execution"], "not_promoted")

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


if __name__ == "__main__":
    unittest.main()
