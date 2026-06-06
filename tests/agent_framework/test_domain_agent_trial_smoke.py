import unittest

from backend.scripts.domain_agent_trial_smoke import build_trial_pack, load_payload


class DomainAgentTrialSmokeTests(unittest.TestCase):
    def test_trial_pack_go_with_ready_evidence(self):
        report = build_trial_pack(_ready_payload())

        self.assertEqual(report["contract_version"], "domain-agent-minimal-integration-trial-pack-v1")
        self.assertEqual(report["overall_status"], "go")
        self.assertEqual(report["stage_statuses"]["trial"], "go")
        self.assertEqual(report["stage_statuses"]["package"], "ready")
        self.assertEqual(report["stage_statuses"]["composition"], "ready")
        self.assertTrue(report["preview_available"])
        self.assertFalse(report["boundary"]["runtime_behavior_changed"])

    def test_trial_pack_review_when_promptops_evidence_is_missing(self):
        payload = _ready_payload()
        payload.pop("promptops_evidence")

        report = build_trial_pack(payload)

        self.assertEqual(report["overall_status"], "review")
        self.assertEqual(report["stage_statuses"]["trial"], "review")
        self.assertTrue(report["warnings"])

    def test_trial_pack_blocked_when_provider_is_degraded(self):
        payload = _ready_payload()
        payload["provider_evidence"] = {"status": "degraded"}

        report = build_trial_pack(payload)

        self.assertEqual(report["overall_status"], "blocked")
        self.assertEqual(report["stage_statuses"]["trial"], "blocked")
        self.assertTrue(report["blockers"])

    def test_checked_in_example_payload_runs(self):
        report = build_trial_pack(load_payload("docs/examples/domain_agent_trial_payload.json"))

        self.assertEqual(report["overall_status"], "go")
        self.assertEqual(report["agent_id"], "ecommerce_support")


def _ready_payload():
    return {
        "agent_id": "ecommerce_support",
        "domain": "refund.policy",
        "query": "What refund policy applies to this order?",
        "evidence_pack": {
            "status": "answerable",
            "allowed_citations": ["refund_policy_2026#section-3"],
        },
        "provider_evidence": {"status": "trial_passed"},
        "promptops_evidence": {"prompt_key": "refund_policy", "version": "2", "status": "active"},
        "memoryops_evidence": {"retrieved_knowledge_promotion_mode": "explicit_only"},
        "eval_evidence": {"overall_status": "passed"},
    }


if __name__ == "__main__":
    unittest.main()
