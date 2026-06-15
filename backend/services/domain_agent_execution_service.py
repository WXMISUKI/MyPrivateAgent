"""Domain Agent Execution Service — bridges agent manifests to SDK execution.

This service reads domain agent manifests (agent.yaml) and creates
AgentHarnessFacade instances with registered tools, enabling domain
agents to be executed through the SDK path.

Usage:
    service = get_domain_agent_execution_service()
    result = service.execute("weather_assistant", input="北京天气怎么样？")
"""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from services.domain_agent_registry_service import get_domain_agent_registry_service
except ModuleNotFoundError:  # pragma: no cover
    from backend.services.domain_agent_registry_service import get_domain_agent_registry_service

logger = logging.getLogger(__name__)

# Domain agents base directory
_AGENTS_DIR = Path(__file__).resolve().parent.parent / "domain_agents"


class DomainAgentExecutionService:
    """Execute domain agents through the SDK path."""

    def __init__(self) -> None:
        self._facade_cache: Dict[str, Any] = {}

    def execute(
        self,
        agent_id: str,
        *,
        input_text: str,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a domain agent through the SDK path.

        Parameters
        ----------
        agent_id:
            The domain agent ID (matches directory name under domain_agents/).
        input_text:
            User input text.
        model_name:
            Optional model override. Defaults to agent manifest's default_model.
        metadata:
            Optional additional metadata to pass to the run.

        Returns
        -------
        Dict with keys: output, events, run, ok.
        """
        facade = self._get_or_create_facade(agent_id)
        if facade is None:
            return {"ok": False, "error": f"Agent '{agent_id}' not found or has no tools."}

        # Determine model name
        manifest = self._load_manifest(agent_id)
        effective_model = model_name or (manifest.get("runtime", {}).get("default_model") if manifest else None) or "doubao"

        # Build run metadata
        run_metadata: Dict[str, Any] = {"agent_id": agent_id}
        if manifest:
            run_metadata["agent_name"] = manifest.get("name", agent_id)
            run_metadata["agent_version"] = manifest.get("version", "0.0.0")
        if metadata:
            run_metadata.update(metadata)

        # Create run
        run = facade.run({
            "run_kind": "chat",
            "input": input_text,
            "metadata": run_metadata,
        })
        run_id = run["run"]["run_id"]

        # Execute
        try:
            result = facade.execute(run_id, model_name=effective_model)
        except Exception as exc:
            logger.exception("Domain agent execution failed: %s", exc)
            return {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "run_id": run_id,
            }

        # Extract output
        model_evidence = result["run"].get("metadata", {}).get("execution_model_step", {})
        output_text = model_evidence.get("text", "")

        return {
            "ok": result["run"]["state"] == "done",
            "output": output_text,
            "events": result["events"],
            "run": result["run"],
            "run_id": run_id,
        }

    def _get_or_create_facade(self, agent_id: str) -> Any:
        """Get or create an AgentHarnessFacade for the given agent."""
        if agent_id in self._facade_cache:
            return self._facade_cache[agent_id]

        manifest = self._load_manifest(agent_id)
        if manifest is None:
            return None

        # Import tools module
        tools_module = self._load_tools_module(agent_id)
        if tools_module is None:
            logger.warning("No tools module found for agent '%s'", agent_id)
            return None

        # Create facade
        try:
            from agent_framework.harness import AgentHarnessFacade
        except ModuleNotFoundError:
            from backend.agent_framework.harness import AgentHarnessFacade

        facade = AgentHarnessFacade(
            name=agent_id,
            model_name=manifest.get("runtime", {}).get("default_model", "doubao"),
        )

        # Register tools from manifest
        tool_specs = getattr(tools_module, "TOOL_SPECS", {})
        declared_tools = manifest.get("capabilities", {}).get("tools", [])

        for tool_name in declared_tools:
            if tool_name in tool_specs:
                spec = tool_specs[tool_name]
                facade.register_tool(
                    {"name": spec["name"], "description": spec["description"]},
                    handler=spec["handler"],
                )
                logger.debug("Registered tool '%s' for agent '%s'", tool_name, agent_id)
            else:
                logger.warning("Tool '%s' declared in manifest but not found in tools module", tool_name)

        self._facade_cache[agent_id] = facade
        return facade

    def _load_manifest(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent.yaml manifest for the given agent."""
        manifest_path = _AGENTS_DIR / agent_id / "agent.yaml"
        if not manifest_path.exists():
            return None
        try:
            import yaml
            with open(manifest_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback: basic YAML parsing for simple manifests
            return self._parse_simple_yaml(manifest_path)
        except Exception as exc:
            logger.warning("Failed to load manifest for '%s': %s", agent_id, exc)
            return None

    def _load_tools_module(self, agent_id: str) -> Optional[Any]:
        """Dynamically import the tools module for the given agent."""
        module_path = _AGENTS_DIR / agent_id / "tools.py"
        if not module_path.exists():
            return None
        try:
            module_name = f"backend.domain_agents.{agent_id}.tools"
            return importlib.import_module(module_name)
        except ImportError:
            try:
                module_name = f"domain_agents.{agent_id}.tools"
                return importlib.import_module(module_name)
            except ImportError as exc:
                logger.warning("Failed to import tools for agent '%s': %s", agent_id, exc)
                return None

    @staticmethod
    def _parse_simple_yaml(path: Path) -> Dict[str, Any]:
        """Minimal YAML parser for simple flat manifests (fallback)."""
        result: Dict[str, Any] = {}
        current_section = result
        section_stack = [result]

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.rstrip()
                if not stripped or stripped.startswith("#"):
                    continue
                indent = len(line) - len(line.lstrip())
                if ":" in stripped:
                    key, _, value = stripped.partition(":")
                    key = key.strip()
                    value = value.strip()
                    if value:
                        # Scalar value
                        if value.lower() == "true":
                            current_section[key] = True
                        elif value.lower() == "false":
                            current_section[key] = False
                        elif value.replace(".", "", 1).isdigit():
                            current_section[key] = float(value) if "." in value else int(value)
                        else:
                            current_section[key] = value.strip("\"'")
                    else:
                        # New section
                        new_section: Dict[str, Any] = {}
                        current_section[key] = new_section
                        current_section = new_section
                elif stripped.startswith("- "):
                    # List item
                    item = stripped[2:].strip().strip("\"'")
                    # Find the last key added
                    for key in reversed(list(current_section.keys())):
                        if isinstance(current_section[key], list):
                            current_section[key].append(item)
                            break
                    else:
                        pass  # Skip orphan list items

        return result


_service_instance: Optional[DomainAgentExecutionService] = None


def get_domain_agent_execution_service() -> DomainAgentExecutionService:
    """Get the singleton DomainAgentExecutionService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DomainAgentExecutionService()
    return _service_instance
