"""Read-only registry for domain agent manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


CONTRACT_VERSION = "domain-agent-registry-v1"
GROUNDING_POLICY_CONTRACT_VERSION = "agent-grounding-policy-v1"
GROUNDING_POLICY_REGISTRY_CONTRACT_VERSION = "agent-grounding-policy-registry-v1"
DEFAULT_DOMAIN_AGENT_ROOT = Path(__file__).resolve().parents[1] / "domain_agents"
SUPPORTED_FALLBACK_POLICIES = {
    "answer_without_claiming_sources",
    "clarify",
    "refuse",
    "refuse_or_clarify_when_no_evidence",
}
SUPPORTED_SOURCE_ACL_MODES = {
    "agent_manifest",
    "provider_catalog",
    "intersection",
}


@dataclass(frozen=True)
class _ManifestResult:
    agent: Dict[str, Any] | None
    error: Dict[str, Any] | None


class DomainAgentRegistryService:
    """Discover domain agent manifests without importing or executing agent code."""

    def __init__(self, root_path: Path | str | None = None):
        self.root_path = Path(root_path) if root_path is not None else DEFAULT_DOMAIN_AGENT_ROOT

    def build_runtime_contract(self) -> Dict[str, Any]:
        agents: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for manifest_path in self._iter_manifest_paths():
            result = self._load_manifest(manifest_path)
            if result.agent is not None:
                agents.append(result.agent)
            if result.error is not None:
                errors.append(result.error)

        ready_agents = sum(1 for agent in agents if agent.get("status") == "ready")
        invalid_agents = len(errors) + sum(1 for agent in agents if agent.get("status") == "invalid")
        total_agents = len(agents) + len(errors)
        grounding_policy_registry = _build_grounding_policy_registry(agents)
        if total_agents == 0:
            status = "empty"
        elif invalid_agents:
            status = "degraded"
        else:
            status = "ready"

        agents.sort(key=lambda item: str(item.get("id") or ""))
        errors.sort(key=lambda item: str(item.get("manifest_path") or ""))
        return {
            "contract_version": CONTRACT_VERSION,
            "status": status,
            "root_path": str(self.root_path),
            "total_agents": total_agents,
            "ready_agents": ready_agents,
            "invalid_agents": invalid_agents,
            "agents": agents,
            "errors": errors,
            "grounding_policy_registry": grounding_policy_registry,
        }

    def build_rag_source_registry_contract(self) -> Dict[str, Any]:
        return _build_knowledge_source_registry(
            self.build_runtime_contract(),
            registry_key="rag_source_registry",
            capability_key="rag_sources",
            entry_key="source_id",
            contract_version="rag-source-registry-v1",
        )

    def build_knowledge_graph_registry_contract(self) -> Dict[str, Any]:
        return _build_knowledge_source_registry(
            self.build_runtime_contract(),
            registry_key="knowledge_graph_registry",
            capability_key="graph_sources",
            entry_key="graph_id",
            contract_version="knowledge-graph-registry-v1",
        )

    def _iter_manifest_paths(self) -> Iterable[Path]:
        root = self.root_path
        if not root.exists() or not root.is_dir():
            return []
        manifests: List[Path] = []
        for agent_dir in sorted((item for item in root.iterdir() if item.is_dir()), key=lambda item: item.name):
            yaml_path = agent_dir / "agent.yaml"
            yml_path = agent_dir / "agent.yml"
            if yaml_path.exists():
                manifests.append(yaml_path)
            elif yml_path.exists():
                manifests.append(yml_path)
        return manifests

    def _load_manifest(self, manifest_path: Path) -> _ManifestResult:
        try:
            raw_manifest = _load_yaml_mapping(manifest_path)
            agent = self._normalize_manifest(manifest_path, raw_manifest)
            return _ManifestResult(agent=agent, error=None)
        except ValueError as exc:
            return _ManifestResult(
                agent=None,
                error={
                    "status": "invalid",
                    "agent_dir": str(manifest_path.parent),
                    "manifest_path": str(manifest_path),
                    "message": str(exc),
                },
            )

    def _normalize_manifest(self, manifest_path: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
        missing = [field for field in ("id", "name", "version") if not _clean_string(manifest.get(field))]
        roles = _normalize_roles(manifest.get("roles"))
        if not roles:
            missing.append("roles[].id")
        if missing:
            raise ValueError(f"Missing required manifest fields: {', '.join(missing)}")

        capabilities = _normalize_capabilities(manifest.get("capabilities"))
        governance = _normalize_governance(manifest.get("governance"))
        grounding_policy = _normalize_grounding_policy(
            grounding_policy_value=manifest.get("grounding_policy"),
            retrieval_value=manifest.get("retrieval"),
            capabilities=capabilities,
        )
        return {
            "id": _clean_string(manifest.get("id")),
            "name": _clean_string(manifest.get("name")),
            "version": _clean_string(manifest.get("version")),
            "description": _clean_string(manifest.get("description")),
            "status": "ready",
            "roles": roles,
            "runtime": _normalize_mapping(manifest.get("runtime")),
            "capabilities": capabilities,
            "grounding_policy": grounding_policy["policy"],
            "grounding_policy_status": grounding_policy["readiness"],
            "governance": governance,
            "agent_dir": str(manifest_path.parent),
            "manifest_path": str(manifest_path),
        }


def _load_yaml_mapping(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        loaded = _parse_limited_yaml(text)
    else:
        loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, Mapping):
        raise ValueError("Manifest root must be a mapping")
    return loaded


def _normalize_roles(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    roles: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        role_id = _clean_string(item.get("id"))
        if not role_id:
            continue
        roles.append(
            {
                "id": role_id,
                "name": _clean_string(item.get("name")) or role_id,
                "default": bool(item.get("default")),
            }
        )
    return roles


def _normalize_capabilities(value: Any) -> Dict[str, List[str]]:
    mapping = _normalize_mapping(value)
    return {
        "tools": _normalize_string_list(mapping.get("tools")),
        "skills": _normalize_string_list(mapping.get("skills")),
        "mcp_servers": _normalize_string_list(mapping.get("mcp_servers")),
        "rag_sources": _normalize_string_list(mapping.get("rag_sources")),
        "graph_sources": _normalize_string_list(mapping.get("graph_sources")),
    }


def _normalize_grounding_policy(
    *,
    grounding_policy_value: Any,
    retrieval_value: Any,
    capabilities: Mapping[str, List[str]],
) -> Dict[str, Any]:
    grounding_mapping = _normalize_mapping(grounding_policy_value)
    retrieval_mapping = _normalize_mapping(retrieval_value)
    policy_source = None
    if grounding_mapping:
        policy_source = "grounding_policy"
    elif retrieval_mapping:
        policy_source = "retrieval"

    merged_mapping: Dict[str, Any] = dict(retrieval_mapping)
    merged_mapping.update(grounding_mapping)

    require_citations, require_citations_valid = _normalize_optional_bool(merged_mapping.get("require_citations"))
    allow_ungrounded, allow_ungrounded_valid = _normalize_optional_bool(merged_mapping.get("allow_ungrounded"))
    must_use_knowledge_for_domains = _normalize_string_list(
        merged_mapping.get("must_use_knowledge_for_domains")
    )
    fallback_policy, fallback_policy_valid = _normalize_bound_enum(
        merged_mapping.get("fallback_policy"),
        SUPPORTED_FALLBACK_POLICIES,
    )
    source_acl_mode, source_acl_mode_valid = _normalize_bound_enum(
        merged_mapping.get("source_acl_mode"),
        SUPPORTED_SOURCE_ACL_MODES,
    )

    compatibility = {
        "mode": _clean_string(merged_mapping.get("mode")) or None,
        "default_top_k": _normalize_optional_int(merged_mapping.get("default_top_k")),
        "graph_usage": _clean_string(merged_mapping.get("graph_usage")) or None,
        "allowed_filters": _normalize_string_list(merged_mapping.get("allowed_filters")),
    }
    declared_fields = {
        key: value
        for key, value in {
            "require_citations": require_citations,
            "allow_ungrounded": allow_ungrounded,
            "must_use_knowledge_for_domains": must_use_knowledge_for_domains,
            "fallback_policy": fallback_policy,
            "source_acl_mode": source_acl_mode,
        }.items()
        if value not in (None, [], {})
    }
    required_fields = {
        "require_citations": require_citations,
        "allow_ungrounded": allow_ungrounded,
        "must_use_knowledge_for_domains": must_use_knowledge_for_domains,
        "fallback_policy": fallback_policy,
        "source_acl_mode": source_acl_mode,
    } if policy_source == "grounding_policy" else {}
    missing_fields = [
        field
        for field, value in required_fields.items()
        if value in (None, [])
    ]
    invalid_fields = [
        field
        for field, valid in {
            "require_citations": require_citations_valid,
            "allow_ungrounded": allow_ungrounded_valid,
            "fallback_policy": fallback_policy_valid,
            "source_acl_mode": source_acl_mode_valid,
        }.items()
        if not valid and field in declared_fields
    ]
    source_ready = bool(capabilities.get("rag_sources") or capabilities.get("graph_sources"))
    if invalid_fields or missing_fields:
        status = "degraded"
        reason_codes = sorted(set(["invalid_policy_fields", *invalid_fields, *missing_fields]))
    elif policy_source is None and source_ready:
        status = "unknown"
        reason_codes = ["policy_not_declared", "source_readiness_unknown", "provider_catalog_unknown"]
    elif policy_source and source_ready:
        status = "unknown"
        reason_codes = ["source_readiness_unknown", "provider_catalog_unknown"]
    elif policy_source:
        status = "ready"
        reason_codes = []
    else:
        status = "unknown"
        reason_codes = ["policy_not_declared"]

    readiness = {
        "contract_version": GROUNDING_POLICY_REGISTRY_CONTRACT_VERSION,
        "status": status,
        "policy_source": policy_source or "none",
        "enforcement": "visibility_only",
        "provider_catalog_status": "unknown" if source_ready else "not_applicable",
        "source_readiness_status": "unknown" if source_ready else "not_applicable",
        "reason_codes": reason_codes,
        "declared_fields": sorted(declared_fields),
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
    }
    policy = {
        "contract_version": GROUNDING_POLICY_CONTRACT_VERSION,
        "policy_source": policy_source or "none",
        "require_citations": require_citations,
        "allow_ungrounded": allow_ungrounded,
        "must_use_knowledge_for_domains": must_use_knowledge_for_domains,
        "fallback_policy": fallback_policy,
        "source_acl_mode": source_acl_mode,
        "compatibility": compatibility,
        "readiness": readiness,
    }
    return {
        "policy": policy,
        "readiness": readiness,
    }


def _build_knowledge_source_registry(
    domain_contract: Mapping[str, Any],
    *,
    registry_key: str,
    capability_key: str,
    entry_key: str,
    contract_version: str,
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    agents = domain_contract.get("agents") if isinstance(domain_contract, Mapping) else []
    if isinstance(agents, list):
        for agent in agents:
            if not isinstance(agent, Mapping) or agent.get("status") != "ready":
                continue
            capabilities = _normalize_mapping(agent.get("capabilities"))
            for source_id in _normalize_string_list(capabilities.get(capability_key)):
                entries.append(
                    {
                        entry_key: source_id,
                        "agent_id": _clean_string(agent.get("id")),
                        "agent_name": _clean_string(agent.get("name")),
                        "manifest_path": _clean_string(agent.get("manifest_path")),
                    }
                )
    entries.sort(key=lambda item: (str(item.get(entry_key) or ""), str(item.get("agent_id") or "")))
    return {
        "contract_version": contract_version,
        "registry_key": registry_key,
        "status": "ready" if entries else "empty",
        "total_entries": len(entries),
        "entries": entries,
    }


def _normalize_governance(value: Any) -> Dict[str, List[str]]:
    mapping = _normalize_mapping(value)
    return {
        "approval_required": _normalize_string_list(mapping.get("approval_required")),
        "audit_tags": _normalize_string_list(mapping.get("audit_tags")),
    }


def _normalize_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _normalize_optional_bool(value: Any) -> tuple[bool | None, bool]:
    if isinstance(value, bool):
        return value, True
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True, True
        if lowered in {"false", "no", "0"}:
            return False, True
    if value is None:
        return None, True
    return None, False


def _normalize_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_bound_enum(value: Any, allowed_values: set[str]) -> tuple[str | None, bool]:
    candidate = _clean_string(value)
    if not candidate:
        return None, True
    if candidate in allowed_values:
        return candidate, True
    return None, False


def _normalize_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [_clean_string(item) for item in value if _clean_string(item)]


def _clean_string(value: Any) -> str:
    return str(value or "").strip()


def _parse_limited_yaml(text: str) -> Dict[str, Any]:
    lines = [
        (len(line) - len(line.lstrip(" ")), line.strip())
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        return {}
    parsed, index = _parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines) or not isinstance(parsed, dict):
        raise ValueError("Unsupported YAML manifest structure")
    return parsed


def _parse_yaml_block(lines: List[Tuple[int, str]], index: int, indent: int) -> Tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    if lines[index][0] < indent:
        return {}, index
    if lines[index][1].startswith("- "):
        return _parse_yaml_list(lines, index, indent)
    return _parse_yaml_mapping(lines, index, indent)


def _parse_yaml_mapping(lines: List[Tuple[int, str]], index: int, indent: int) -> Tuple[Dict[str, Any], int]:
    result: Dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation near: {content}")
        if content.startswith("- "):
            break
        key, value = _split_yaml_key_value(content)
        index += 1
        if value == "":
            if index < len(lines) and lines[index][0] > current_indent:
                child, index = _parse_yaml_block(lines, index, lines[index][0])
                result[key] = child
            else:
                result[key] = None
        else:
            result[key] = _parse_yaml_scalar(value)
    return result, index


def _parse_yaml_list(lines: List[Tuple[int, str]], index: int, indent: int) -> Tuple[List[Any], int]:
    result: List[Any] = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not content.startswith("- "):
            break
        item_content = content[2:].strip()
        index += 1
        item: Any
        if item_content == "":
            if index < len(lines) and lines[index][0] > current_indent:
                item, index = _parse_yaml_block(lines, index, lines[index][0])
            else:
                item = None
        elif ":" in item_content:
            key, value = _split_yaml_key_value(item_content)
            item = {key: _parse_yaml_scalar(value)}
            if index < len(lines) and lines[index][0] > current_indent:
                child, index = _parse_yaml_mapping(lines, index, lines[index][0])
                if isinstance(child, dict):
                    item.update(child)
        else:
            item = _parse_yaml_scalar(item_content)
        result.append(item)
    return result, index


def _split_yaml_key_value(content: str) -> Tuple[str, str]:
    if ":" not in content:
        raise ValueError(f"Expected key/value pair near: {content}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Missing key near: {content}")
    return key, value.strip()


def _parse_yaml_scalar(value: str) -> Any:
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


_domain_agent_registry_service: Optional[DomainAgentRegistryService] = None


def get_domain_agent_registry_service() -> DomainAgentRegistryService:
    global _domain_agent_registry_service
    if _domain_agent_registry_service is None:
        _domain_agent_registry_service = DomainAgentRegistryService()
    return _domain_agent_registry_service


def _build_grounding_policy_registry(agents: List[Dict[str, Any]]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for agent in agents:
        if not isinstance(agent, dict) or agent.get("status") != "ready":
            continue
        policy = agent.get("grounding_policy")
        readiness = agent.get("grounding_policy_status")
        if not isinstance(policy, dict) or not isinstance(readiness, dict):
            continue
        entries.append(
            {
                "agent_id": _clean_string(agent.get("id")),
                "agent_name": _clean_string(agent.get("name")),
                "manifest_path": _clean_string(agent.get("manifest_path")),
                "policy_source": _clean_string(policy.get("policy_source")) or "none",
                "status": _clean_string(readiness.get("status")) or "unknown",
                "enforcement": _clean_string(readiness.get("enforcement")) or "visibility_only",
                "reason_codes": list(readiness.get("reason_codes") or []),
                "provider_catalog_status": _clean_string(readiness.get("provider_catalog_status")) or "unknown",
                "source_readiness_status": _clean_string(readiness.get("source_readiness_status")) or "unknown",
                "declared_fields": list(readiness.get("declared_fields") or []),
                "missing_fields": list(readiness.get("missing_fields") or []),
                "invalid_fields": list(readiness.get("invalid_fields") or []),
            }
        )
    entries.sort(key=lambda item: (str(item.get("agent_id") or ""), str(item.get("manifest_path") or "")))
    statuses = {str(entry.get("status") or "unknown") for entry in entries}
    if not entries:
        status = "empty"
    elif "degraded" in statuses:
        status = "degraded"
    elif "unknown" in statuses:
        status = "unknown"
    else:
        status = "ready"
    return {
        "contract_version": GROUNDING_POLICY_REGISTRY_CONTRACT_VERSION,
        "status": status,
        "enforcement": "visibility_only",
        "total_entries": len(entries),
        "ready_entries": sum(1 for entry in entries if entry.get("status") == "ready"),
        "unknown_entries": sum(1 for entry in entries if entry.get("status") == "unknown"),
        "degraded_entries": sum(1 for entry in entries if entry.get("status") == "degraded"),
        "entries": entries,
    }
