"""Read-only API-facing catalog for domain agent assets."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

try:
    from services.domain_agent_registry_service import DomainAgentRegistryService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.domain_agent_registry_service import DomainAgentRegistryService


CONTRACT_VERSION = "domain-agent-catalog-v1"


class DomainAgentCatalogService:
    """Expose a narrow catalog contract over the manifest-driven registry."""

    def __init__(self, registry_service: DomainAgentRegistryService):
        self.registry_service = registry_service

    def build_catalog(self) -> Dict[str, Any]:
        registry = self.registry_service.build_runtime_contract()
        agents = registry.get("agents") if isinstance(registry.get("agents"), list) else []
        errors = registry.get("errors") if isinstance(registry.get("errors"), list) else []
        catalog_agents = [self._catalog_agent(agent) for agent in agents if isinstance(agent, Mapping)]
        return {
            "contract_version": CONTRACT_VERSION,
            "status": registry.get("status") or "empty",
            "source_contract_version": registry.get("contract_version"),
            "total_agents": int(registry.get("total_agents") or 0),
            "ready_agents": int(registry.get("ready_agents") or 0),
            "invalid_agents": int(registry.get("invalid_agents") or 0),
            "agents": catalog_agents,
            "errors": [error for error in errors if isinstance(error, dict)],
        }

    def _catalog_agent(self, agent: Mapping[str, Any]) -> Dict[str, Any]:
        roles = agent.get("roles") if isinstance(agent.get("roles"), list) else []
        capabilities = agent.get("capabilities") if isinstance(agent.get("capabilities"), Mapping) else {}
        tools = _string_list(capabilities.get("tools"))
        skills = _string_list(capabilities.get("skills"))
        mcp_servers = _string_list(capabilities.get("mcp_servers"))
        rag_sources = _string_list(capabilities.get("rag_sources"))
        graph_sources = _string_list(capabilities.get("graph_sources"))
        grounding_policy = agent.get("grounding_policy") if isinstance(agent.get("grounding_policy"), Mapping) else {}
        grounding_status = (
            agent.get("grounding_policy_status")
            if isinstance(agent.get("grounding_policy_status"), Mapping)
            else {}
        )
        return {
            "id": str(agent.get("id") or ""),
            "name": str(agent.get("name") or ""),
            "version": str(agent.get("version") or ""),
            "description": str(agent.get("description") or ""),
            "status": str(agent.get("status") or "unknown"),
            "roles": [role for role in roles if isinstance(role, dict)],
            "default_role_id": _default_role_id(roles),
            "capabilities": {
                "tools": tools,
                "skills": skills,
                "mcp_servers": mcp_servers,
                "rag_sources": rag_sources,
                "graph_sources": graph_sources,
            },
            "capability_counts": {
                "tools": len(tools),
                "skills": len(skills),
                "mcp_servers": len(mcp_servers),
                "rag_sources": len(rag_sources),
                "graph_sources": len(graph_sources),
            },
            "grounding_policy": {
                "policy_source": grounding_policy.get("policy_source") or "none",
                "require_citations": grounding_policy.get("require_citations"),
                "allow_ungrounded": grounding_policy.get("allow_ungrounded"),
                "must_use_knowledge_for_domains": _string_list(
                    grounding_policy.get("must_use_knowledge_for_domains")
                ),
                "fallback_policy": grounding_policy.get("fallback_policy"),
                "source_acl_mode": grounding_policy.get("source_acl_mode"),
            },
            "grounding_policy_status": {
                "status": grounding_status.get("status") or "unknown",
                "enforcement": grounding_status.get("enforcement") or "visibility_only",
                "reason_codes": _string_list(grounding_status.get("reason_codes")),
                "provider_catalog_status": grounding_status.get("provider_catalog_status") or "unknown",
                "source_readiness_status": grounding_status.get("source_readiness_status") or "unknown",
            },
        }


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _default_role_id(value: Any) -> Optional[str]:
    if not isinstance(value, list):
        return None
    for role in value:
        if isinstance(role, Mapping) and role.get("default") is True and role.get("id"):
            return str(role.get("id"))
    return None


_domain_agent_catalog_service: Optional[DomainAgentCatalogService] = None


def get_domain_agent_catalog_service() -> DomainAgentCatalogService:
    global _domain_agent_catalog_service
    if _domain_agent_catalog_service is None:
        try:
            from services.domain_agent_registry_service import get_domain_agent_registry_service
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.services.domain_agent_registry_service import get_domain_agent_registry_service

        _domain_agent_catalog_service = DomainAgentCatalogService(get_domain_agent_registry_service())
    return _domain_agent_catalog_service
