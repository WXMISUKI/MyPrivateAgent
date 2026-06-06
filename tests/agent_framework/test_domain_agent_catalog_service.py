import unittest

from backend.services.domain_agent_catalog_service import DomainAgentCatalogService


class StubRegistryService:
    def __init__(self, contract):
        self.contract = contract

    def build_runtime_contract(self):
        return self.contract


class DomainAgentCatalogServiceTests(unittest.TestCase):
    def test_build_catalog_returns_ready_agent_summary(self):
        service = DomainAgentCatalogService(
            StubRegistryService(
                {
                    "contract_version": "domain-agent-registry-v1",
                    "status": "ready",
                    "total_agents": 1,
                    "ready_agents": 1,
                    "invalid_agents": 0,
                    "agents": [
                        {
                            "id": "ecommerce_support",
                            "name": "Ecommerce Support",
                            "version": "0.1.0",
                            "description": "Handles refund policy questions.",
                            "status": "ready",
                            "roles": [
                                {"id": "after_sales_specialist", "name": "After Sales", "default": True},
                                {"id": "logistics_specialist", "name": "Logistics", "default": False},
                            ],
                            "capabilities": {
                                "tools": ["order.lookup", "refund.create_request"],
                                "skills": ["refund_policy"],
                                "mcp_servers": ["ecommerce_order_mcp"],
                                "rag_sources": ["refund_policy_docs"],
                                "graph_sources": [],
                            },
                            "grounding_policy": {
                                "policy_source": "grounding_policy",
                                "require_citations": True,
                                "allow_ungrounded": False,
                                "must_use_knowledge_for_domains": ["refund.policy"],
                                "fallback_policy": "refuse_or_clarify_when_no_evidence",
                                "source_acl_mode": "agent_manifest",
                            },
                            "grounding_policy_status": {
                                "status": "ready",
                                "enforcement": "visibility_only",
                                "reason_codes": [],
                                "provider_catalog_status": "not_applicable",
                                "source_readiness_status": "not_applicable",
                            },
                        }
                    ],
                    "errors": [],
                }
            )
        )

        catalog = service.build_catalog()

        self.assertEqual(catalog["contract_version"], "domain-agent-catalog-v1")
        self.assertEqual(catalog["status"], "ready")
        self.assertEqual(catalog["agents"][0]["default_role_id"], "after_sales_specialist")
        self.assertEqual(catalog["agents"][0]["capability_counts"]["tools"], 2)
        self.assertTrue(catalog["agents"][0]["grounding_policy"]["require_citations"])

    def test_build_catalog_preserves_empty_shape(self):
        service = DomainAgentCatalogService(
            StubRegistryService(
                {
                    "contract_version": "domain-agent-registry-v1",
                    "status": "empty",
                    "total_agents": 0,
                    "ready_agents": 0,
                    "invalid_agents": 0,
                    "agents": [],
                    "errors": [],
                }
            )
        )

        catalog = service.build_catalog()

        self.assertEqual(catalog["status"], "empty")
        self.assertEqual(catalog["agents"], [])
        self.assertEqual(catalog["errors"], [])

    def test_build_catalog_preserves_invalid_manifest_errors(self):
        service = DomainAgentCatalogService(
            StubRegistryService(
                {
                    "contract_version": "domain-agent-registry-v1",
                    "status": "degraded",
                    "total_agents": 1,
                    "ready_agents": 0,
                    "invalid_agents": 1,
                    "agents": [],
                    "errors": [
                        {
                            "status": "invalid",
                            "manifest_path": "backend/domain_agents/broken/agent.yaml",
                            "message": "Missing required manifest fields: name",
                        }
                    ],
                }
            )
        )

        catalog = service.build_catalog()

        self.assertEqual(catalog["status"], "degraded")
        self.assertEqual(catalog["invalid_agents"], 1)
        self.assertEqual(catalog["errors"][0]["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
