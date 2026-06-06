import unittest

from backend.services.domain_agent_capability_linkage_service import (
    DomainAgentCapabilityLinkageService,
)


class StubToolRuntimeService:
    def __init__(self, tools=None, error=None):
        self.tools = tools or []
        self.error = error

    def build_runtime_contract(self):
        if self.error:
            raise RuntimeError(self.error)
        return {"tools": [{"name": name} for name in self.tools]}


class StubSkillRuntimeService:
    def __init__(self, skills=None, error=None):
        self.skills = skills or []
        self.error = error

    def build_runtime_contract(self):
        if self.error:
            raise RuntimeError(self.error)
        return {"definitions": [{"name": name} for name in self.skills]}


class StubMcpRegistryService:
    def __init__(self, servers=None, error=None):
        self.servers = servers or []
        self.error = error

    def list_servers(self):
        if self.error:
            raise RuntimeError(self.error)
        return self.servers


class DomainAgentCapabilityLinkageServiceTests(unittest.TestCase):
    def test_build_linkage_marks_declared_capabilities_ready(self):
        service = DomainAgentCapabilityLinkageService(
            tool_runtime_service=StubToolRuntimeService(["order.lookup"]),
            skill_runtime_service=StubSkillRuntimeService(["refund_policy"]),
            mcp_registry_service=StubMcpRegistryService(
                [
                    {
                        "name": "ecommerce-order-mcp",
                        "enabled": True,
                        "capabilities": ["order.read"],
                    }
                ]
            ),
        )

        linkage = service.build_linkage(
            {
                "tools": ["order.lookup"],
                "skills": ["refund_policy"],
                "mcp_servers": ["ecommerce-order-mcp", "order.read"],
            }
        )

        self.assertEqual(linkage["contract_version"], "domain-agent-capability-linkage-readiness-v1")
        self.assertEqual(linkage["status"], "ready")
        self.assertEqual(linkage["tools"]["missing"], [])
        self.assertEqual(linkage["skills"]["resolved"], ["refund_policy"])
        self.assertEqual(linkage["mcp_servers"]["resolved_servers"], ["ecommerce-order-mcp"])
        self.assertEqual(linkage["mcp_servers"]["resolved_capabilities"], ["order.read"])
        self.assertFalse(linkage["boundary"]["runtime_behavior_changed"])

    def test_build_linkage_marks_missing_or_disabled_capabilities_for_review(self):
        service = DomainAgentCapabilityLinkageService(
            tool_runtime_service=StubToolRuntimeService(["order.lookup"]),
            skill_runtime_service=StubSkillRuntimeService(["refund_policy"]),
            mcp_registry_service=StubMcpRegistryService(
                [{"name": "disabled-order-mcp", "enabled": False, "capabilities": ["order.read"]}]
            ),
        )

        linkage = service.build_linkage(
            {
                "tools": ["order.lookup", "refund.create_request"],
                "skills": ["refund_policy", "logistics_diagnosis"],
                "mcp_servers": ["disabled-order-mcp", "missing-order-mcp"],
            }
        )

        self.assertEqual(linkage["status"], "review")
        self.assertEqual(linkage["recommended_action"], "review_manifest_capability_declarations")
        self.assertEqual(linkage["tools"]["missing"], ["refund.create_request"])
        self.assertEqual(linkage["skills"]["missing"], ["logistics_diagnosis"])
        self.assertEqual(linkage["mcp_servers"]["missing"], ["missing-order-mcp"])
        self.assertEqual(linkage["mcp_servers"]["disabled_servers"], ["disabled-order-mcp"])

    def test_build_linkage_keeps_rag_and_graph_sources_external_not_checked(self):
        service = DomainAgentCapabilityLinkageService(
            tool_runtime_service=StubToolRuntimeService(),
            skill_runtime_service=StubSkillRuntimeService(),
            mcp_registry_service=StubMcpRegistryService(),
        )

        linkage = service.build_linkage(
            {
                "rag_sources": ["refund_policy_docs"],
                "graph_sources": ["ecommerce_order_graph"],
            }
        )

        self.assertEqual(linkage["status"], "ready")
        self.assertEqual(linkage["rag_sources"]["status"], "not_checked")
        self.assertEqual(linkage["graph_sources"]["owner"], "external_provider")
        self.assertEqual(linkage["boundary"]["rag_graph_source_validation"], "external_provider_boundary")


if __name__ == "__main__":
    unittest.main()
