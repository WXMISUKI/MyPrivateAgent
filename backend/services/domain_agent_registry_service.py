"""Read-only registry for domain agent manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


CONTRACT_VERSION = "domain-agent-registry-v1"
DEFAULT_DOMAIN_AGENT_ROOT = Path(__file__).resolve().parents[1] / "domain_agents"


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
        }

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
        return {
            "id": _clean_string(manifest.get("id")),
            "name": _clean_string(manifest.get("name")),
            "version": _clean_string(manifest.get("version")),
            "description": _clean_string(manifest.get("description")),
            "status": "ready",
            "roles": roles,
            "runtime": _normalize_mapping(manifest.get("runtime")),
            "capabilities": capabilities,
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
    }


def _normalize_governance(value: Any) -> Dict[str, List[str]]:
    mapping = _normalize_mapping(value)
    return {
        "approval_required": _normalize_string_list(mapping.get("approval_required")),
        "audit_tags": _normalize_string_list(mapping.get("audit_tags")),
    }


def _normalize_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


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
