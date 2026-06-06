"""Read-only linkage readiness for domain agent manifest capabilities."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Set, Tuple


CONTRACT_VERSION = "domain-agent-capability-linkage-readiness-v1"


class DomainAgentCapabilityLinkageService:
    """Compare manifest-declared capabilities with current read-only registries."""

    def __init__(
        self,
        *,
        tool_runtime_service: Any = None,
        skill_runtime_service: Any = None,
        mcp_registry_service: Any = None,
    ):
        self.tool_runtime_service = tool_runtime_service or _get_tool_runtime_service()
        self.skill_runtime_service = skill_runtime_service or _get_skill_runtime_service()
        self.mcp_registry_service = mcp_registry_service or _get_mcp_registry_service()

    def build_linkage(self, capabilities: Mapping[str, Any]) -> Dict[str, Any]:
        normalized = capabilities if isinstance(capabilities, Mapping) else {}
        tools = _string_list(normalized.get("tools"))
        skills = _string_list(normalized.get("skills"))
        mcp_refs = _string_list(normalized.get("mcp_servers"))
        rag_sources = _string_list(normalized.get("rag_sources"))
        graph_sources = _string_list(normalized.get("graph_sources"))

        tool_names, tool_error = self._available_tool_names()
        skill_names, skill_error = self._available_skill_names()
        mcp_servers, mcp_capabilities, mcp_error = self._available_mcp_references()

        tool_linkage = _local_family(
            declared=tools,
            available=tool_names,
            family="tools",
            registry_error=tool_error,
        )
        skill_linkage = _local_family(
            declared=skills,
            available=skill_names,
            family="skills",
            registry_error=skill_error,
        )
        mcp_linkage = self._mcp_family(
            declared=mcp_refs,
            server_map=mcp_servers,
            capability_map=mcp_capabilities,
            registry_error=mcp_error,
        )
        local_families = [tool_linkage, skill_linkage, mcp_linkage]
        status = "review" if any(item["status"] == "review" for item in local_families) else "ready"
        return {
            "contract_version": CONTRACT_VERSION,
            "status": status,
            "recommended_action": (
                "review_manifest_capability_declarations"
                if status == "review"
                else "no_action_required"
            ),
            "tools": tool_linkage,
            "skills": skill_linkage,
            "mcp_servers": mcp_linkage,
            "rag_sources": _external_family(rag_sources, "rag_sources"),
            "graph_sources": _external_family(graph_sources, "graph_sources"),
            "boundary": {
                "read_only": True,
                "tool_registration": "not_performed",
                "skill_activation": "not_performed",
                "mcp_server_enablement": "not_performed",
                "rag_graph_source_validation": "external_provider_boundary",
                "runtime_behavior_changed": False,
            },
        }

    def _available_tool_names(self) -> Tuple[Set[str], str]:
        try:
            contract = self.tool_runtime_service.build_runtime_contract()
        except Exception as exc:  # pragma: no cover - defensive registry boundary
            return set(), str(exc)
        tools = contract.get("tools") if isinstance(contract, Mapping) else []
        return {
            str(item.get("name") or "").strip()
            for item in tools
            if isinstance(item, Mapping) and str(item.get("name") or "").strip()
        }, ""

    def _available_skill_names(self) -> Tuple[Set[str], str]:
        try:
            contract = self.skill_runtime_service.build_runtime_contract()
        except Exception as exc:  # pragma: no cover - defensive registry boundary
            return set(), str(exc)
        definitions = contract.get("definitions") if isinstance(contract, Mapping) else []
        return {
            str(item.get("name") or "").strip()
            for item in definitions
            if isinstance(item, Mapping) and str(item.get("name") or "").strip()
        }, ""

    def _available_mcp_references(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]], str]:
        try:
            servers = self.mcp_registry_service.list_servers()
        except Exception as exc:  # pragma: no cover - defensive registry boundary
            return {}, {}, str(exc)
        server_map: Dict[str, Dict[str, Any]] = {}
        capability_map: Dict[str, List[str]] = {}
        for server in servers if isinstance(servers, list) else []:
            if not isinstance(server, Mapping):
                continue
            name = str(server.get("name") or "").strip()
            if not name:
                continue
            capabilities = _string_list(server.get("capabilities"))
            server_map[name] = {
                "enabled": bool(server.get("enabled")),
                "capabilities": capabilities,
            }
            for capability in capabilities:
                capability_map.setdefault(capability, []).append(name)
        return server_map, {key: sorted(value) for key, value in capability_map.items()}, ""

    def _mcp_family(
        self,
        *,
        declared: List[str],
        server_map: Mapping[str, Mapping[str, Any]],
        capability_map: Mapping[str, List[str]],
        registry_error: str,
    ) -> Dict[str, Any]:
        resolved_servers: List[str] = []
        resolved_capabilities: List[str] = []
        disabled_servers: List[str] = []
        missing: List[str] = []
        for item in declared:
            server = server_map.get(item)
            if server is not None:
                resolved_servers.append(item)
                if not server.get("enabled"):
                    disabled_servers.append(item)
                continue
            if item in capability_map:
                resolved_capabilities.append(item)
                continue
            missing.append(item)

        status = "not_declared"
        if declared:
            status = "review" if missing or disabled_servers or registry_error else "ready"
        return {
            "status": status,
            "declared": declared,
            "resolved": sorted(resolved_servers + resolved_capabilities),
            "resolved_servers": sorted(resolved_servers),
            "resolved_capabilities": sorted(resolved_capabilities),
            "missing": missing,
            "disabled_servers": sorted(disabled_servers),
            "registry_error": registry_error,
            "owner": "myprivateagent_capability_layer",
            "recommended_action": (
                "review_manifest_capability_declarations"
                if status == "review"
                else "no_action_required"
            ),
        }


def _local_family(
    *,
    declared: List[str],
    available: Set[str],
    family: str,
    registry_error: str,
) -> Dict[str, Any]:
    resolved = [item for item in declared if item in available]
    missing = [item for item in declared if item not in available]
    status = "not_declared"
    if declared:
        status = "review" if missing or registry_error else "ready"
    return {
        "status": status,
        "declared": declared,
        "resolved": resolved,
        "missing": missing,
        "registry_error": registry_error,
        "owner": "myprivateagent_capability_layer",
        "recommended_action": (
            "review_manifest_capability_declarations"
            if status == "review"
            else "no_action_required"
        ),
        "family": family,
    }


def _external_family(declared: List[str], family: str) -> Dict[str, Any]:
    return {
        "status": "not_checked" if declared else "not_declared",
        "declared": declared,
        "resolved": [],
        "missing": [],
        "owner": "external_provider",
        "recommended_action": "confirm_external_provider_readiness" if declared else "no_action_required",
        "family": family,
    }


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _get_tool_runtime_service() -> Any:
    try:
        from services.tool_runtime_service import get_tool_runtime_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.tool_runtime_service import get_tool_runtime_service
    return get_tool_runtime_service()


def _get_skill_runtime_service() -> Any:
    try:
        from services.skill_runtime_service import get_skill_runtime_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.skill_runtime_service import get_skill_runtime_service
    return get_skill_runtime_service()


def _get_mcp_registry_service() -> Any:
    try:
        from services.mcp_registry_service import get_mcp_registry_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.mcp_registry_service import get_mcp_registry_service
    return get_mcp_registry_service()


_domain_agent_capability_linkage_service: Optional[DomainAgentCapabilityLinkageService] = None


def get_domain_agent_capability_linkage_service() -> DomainAgentCapabilityLinkageService:
    global _domain_agent_capability_linkage_service
    if _domain_agent_capability_linkage_service is None:
        _domain_agent_capability_linkage_service = DomainAgentCapabilityLinkageService()
    return _domain_agent_capability_linkage_service
