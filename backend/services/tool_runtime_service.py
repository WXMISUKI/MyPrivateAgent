"""Tool runtime contract and adapter health surface for Phase B."""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Dict, Iterable, List, Optional

try:
    from harness.tool_registry import get_registry
    from agent_framework.framework_adapters import get_framework_adapter_registry
    from services.mcp_registry_service import get_mcp_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.harness.tool_registry import get_registry
    from backend.agent_framework.framework_adapters import get_framework_adapter_registry
    from backend.services.mcp_registry_service import get_mcp_registry_service


class ToolRuntimeService:
    """Expose a stable capability-layer contract for registered tools and adapters."""

    def __init__(
        self,
        *,
        tool_registry: Any = None,
        mcp_registry_service: Any = None,
        framework_adapter_registry: Any = None,
    ):
        self.tool_registry = tool_registry or get_registry()
        self.mcp_registry_service = mcp_registry_service or get_mcp_registry_service()
        self.framework_adapter_registry = framework_adapter_registry or get_framework_adapter_registry()
        self._last_registry_errors: Dict[str, str] = {}
        self._last_mcp_error = ""

    def build_runtime_contract(self) -> Dict[str, Any]:
        self._last_registry_errors = {}
        self._last_mcp_error = ""
        base_tools = self._safe_list(self.tool_registry, "list_all")
        langchain_tools = self._safe_list(self.tool_registry, "get_langchain_tools")
        tool_specs = self._safe_list(self.tool_registry, "list_tool_specs")
        doubao_definitions = self._safe_list(self.tool_registry, "get_doubao_tool_definitions")
        mcp_capabilities = self._list_mcp_capabilities()
        tool_entries = self._build_tool_entries(
            base_tools=base_tools,
            langchain_tools=langchain_tools,
            tool_specs=tool_specs,
        )

        return {
            "contract_version": "phase-b-tool-runtime-v1",
            "execution_adapter": {
                "contract_version": "phase-ii-tool-runtime-execution-v1",
                "available": True,
                "action_observation_envelope": True,
                "schema_validation": "lightweight_schema_v1",
                "schema_validation_keywords": ["required", "type", "enum", "object.required"],
                "timeout_enforcement": "post_call_elapsed_check",
                "retry_policy": "sync_exception_retry",
                "policy_coordination": "permission_level_gate_v1",
                "policy_decision_statuses": ["allowed", "approval_required", "denied"],
            },
            "total_tools": len(tool_entries),
            "base_tool_count": len(base_tools),
            "langchain_tool_count": len(langchain_tools),
            "tool_spec_count": len(tool_specs),
            "doubao_definition_count": len(doubao_definitions),
            "mcp_capability_count": len(mcp_capabilities),
            "high_risk_tool_count": len([item for item in tool_entries if item["risk_level"] == "high"]),
            "tool_registry_status": "unavailable" if self._last_registry_errors else "healthy",
            "tool_registry_error": "; ".join(self._last_registry_errors.values()) if self._last_registry_errors else "",
            "mcp_registry_status": "unavailable" if self._last_mcp_error else ("healthy" if mcp_capabilities else "not_configured"),
            "mcp_registry_error": self._last_mcp_error,
            "tools": tool_entries,
            "mcp_capabilities": mcp_capabilities,
        }

    def build_adapter_health_contract(self) -> Dict[str, Any]:
        runtime_contract = self.build_runtime_contract()
        adapters = [
            {
                "adapter_id": "tool_registry",
                "display_name": "Tool Registry",
                "adapter_type": "internal",
                "status": runtime_contract["tool_registry_status"],
                "detail": runtime_contract["tool_registry_error"] or f"{runtime_contract['total_tools']} tools registered",
                "configuration_status": "ready" if runtime_contract["tool_registry_status"] == "healthy" else runtime_contract["tool_registry_status"],
                "package_installed": True,
                "runtime_enabled": True,
                "execution_mode": "internal_registry",
                "required_env": [],
                "missing_env": [],
                "required_packages": [],
                "missing_packages": [],
                "execution_block_reason": runtime_contract["tool_registry_error"] or "",
            },
            {
                "adapter_id": "mcp_runtime",
                "display_name": "MCP Runtime",
                "adapter_type": "mcp",
                "status": runtime_contract["mcp_registry_status"],
                "detail": runtime_contract["mcp_registry_error"] or f"{runtime_contract['mcp_capability_count']} capabilities available",
                "configuration_status": "ready" if runtime_contract["mcp_registry_status"] == "healthy" else runtime_contract["mcp_registry_status"],
                "package_installed": True,
                "runtime_enabled": runtime_contract["mcp_registry_status"] == "healthy",
                "execution_mode": "internal_runtime",
                "required_env": [],
                "missing_env": [],
                "required_packages": [],
                "missing_packages": [],
                "execution_block_reason": runtime_contract["mcp_registry_error"] or "",
            },
        ]
        framework_adapters = self._list_framework_adapter_health()
        adapters.extend(framework_adapters or [{
            "adapter_id": "external_frameworks",
            "display_name": "External Framework Adapters",
            "adapter_type": "agent_framework",
            "status": "not_configured",
            "detail": "LangGraph / DeepAgents-style / CrewAI-style adapters are reserved but not enabled.",
            "configuration_status": "not_configured",
            "package_installed": False,
            "runtime_enabled": False,
            "execution_mode": "placeholder",
            "required_env": [],
            "missing_env": [],
            "required_packages": [],
            "missing_packages": [],
            "execution_block_reason": "external framework adapters are reserved but not enabled",
        }])
        unavailable_count = len([item for item in adapters if item["status"] in {"unhealthy", "unavailable"}])
        not_configured_count = len([item for item in adapters if item["status"] == "not_configured"])
        overall_status = "degraded" if unavailable_count else ("not_configured" if not_configured_count else "healthy")
        return {
            "contract_version": "phase-b-adapter-health-v1",
            "overall_status": overall_status,
            "adapter_count": len(adapters),
            "unavailable_count": unavailable_count,
            "not_configured_count": not_configured_count,
            "adapters": adapters,
        }

    def execute_tool(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        *,
        execution_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized_tool_name = str(tool_name or "").strip()
        tool_args = dict(args or {})
        options = dict(execution_options or {})
        if not normalized_tool_name:
            return self._build_tool_execution_result(
                status="not_found",
                tool_name="",
                args=tool_args,
                result_text="",
                schema_validation={"status": "skipped", "missing_required": []},
                retry=self._build_retry_metadata(status="skipped", attempt_count=0, max_attempts=0),
                timeout=self._build_timeout_metadata(status="skipped", timeout_seconds=None, elapsed_seconds=0.0),
                policy_decision=self._build_policy_decision(
                    status="skipped",
                    tool_name="",
                    permission_level="unknown",
                    reason_code="tool_name_required",
                ),
                observation_status="not_found",
                error="tool_name is required",
            )

        tool = self._get_registry_tool(normalized_tool_name)
        tool_spec = self._get_registry_tool_spec(normalized_tool_name)
        max_attempts = self._normalize_max_attempts(options.get("max_attempts"))
        timeout_seconds = self._resolve_timeout_seconds(options.get("timeout_seconds"), tool_spec)
        if tool is None:
            return self._build_tool_execution_result(
                status="not_found",
                tool_name=normalized_tool_name,
                args=tool_args,
                result_text="",
                tool_spec=tool_spec,
                schema_validation={"status": "skipped", "missing_required": []},
                retry=self._build_retry_metadata(status="skipped", attempt_count=0, max_attempts=max_attempts),
                timeout=self._build_timeout_metadata(status="skipped", timeout_seconds=timeout_seconds, elapsed_seconds=0.0),
                policy_decision=self._build_policy_decision(
                    status="skipped",
                    tool_name=normalized_tool_name,
                    permission_level="unknown",
                    reason_code="tool_not_registered",
                ),
                observation_status="not_found",
                error=f"tool `{normalized_tool_name}` is not registered",
            )

        policy_decision = self._evaluate_tool_policy(
            tool=tool,
            tool_spec=tool_spec,
            tool_name=normalized_tool_name,
        )
        policy_override = self._normalize_policy_override(options.get("policy_override"))
        if (
            policy_decision["status"] == "approval_required"
            and policy_override.get("status") == "approved"
        ):
            policy_decision = self._build_approved_policy_decision(
                original_decision=policy_decision,
                override=policy_override,
            )
        if policy_decision["status"] == "approval_required":
            return self._build_tool_execution_result(
                status="approval_required",
                tool_name=normalized_tool_name,
                args=tool_args,
                result_text="",
                tool_spec=tool_spec,
                schema_validation={"status": "skipped", "missing_required": []},
                retry=self._build_retry_metadata(status="skipped", attempt_count=0, max_attempts=max_attempts),
                timeout=self._build_timeout_metadata(status="skipped", timeout_seconds=timeout_seconds, elapsed_seconds=0.0),
                policy_decision=policy_decision,
                observation_status="approval_required",
                error=policy_decision["reason"],
            )
        if policy_decision["status"] == "denied":
            return self._build_tool_execution_result(
                status="policy_denied",
                tool_name=normalized_tool_name,
                args=tool_args,
                result_text="",
                tool_spec=tool_spec,
                schema_validation={"status": "skipped", "missing_required": []},
                retry=self._build_retry_metadata(status="skipped", attempt_count=0, max_attempts=max_attempts),
                timeout=self._build_timeout_metadata(status="skipped", timeout_seconds=timeout_seconds, elapsed_seconds=0.0),
                policy_decision=policy_decision,
                observation_status="policy_denied",
                error=policy_decision["reason"],
            )

        schema_validation = self._validate_tool_args(tool, tool_args)
        if schema_validation["status"] != "passed":
            return self._build_tool_execution_result(
                status="validation_failed",
                tool_name=normalized_tool_name,
                args=tool_args,
                result_text="",
                tool_spec=tool_spec,
                schema_validation=schema_validation,
                retry=self._build_retry_metadata(status="skipped", attempt_count=0, max_attempts=max_attempts),
                timeout=self._build_timeout_metadata(status="skipped", timeout_seconds=timeout_seconds, elapsed_seconds=0.0),
                policy_decision=policy_decision,
                observation_status="validation_failed",
                error="missing required tool arguments",
            )

        errors: List[str] = []
        for attempt in range(1, max_attempts + 1):
            started_at = time.monotonic()
            try:
                raw_result = self._invoke_tool(tool, tool_args)
            except Exception as exc:  # pragma: no cover - exact tool exception type belongs to tool implementation.
                errors.append(str(exc))
                if attempt < max_attempts:
                    continue
                return self._build_tool_execution_result(
                    status="error",
                    tool_name=normalized_tool_name,
                    args=tool_args,
                    result_text="",
                    tool_spec=tool_spec,
                    schema_validation=schema_validation,
                    retry=self._build_retry_metadata(
                        status="exhausted" if max_attempts > 1 else "not_retried",
                        attempt_count=attempt,
                        max_attempts=max_attempts,
                        errors=errors,
                    ),
                    timeout=self._build_timeout_metadata(
                        status="not_configured" if timeout_seconds is None else "not_exceeded",
                        timeout_seconds=timeout_seconds,
                        elapsed_seconds=time.monotonic() - started_at,
                    ),
                    policy_decision=policy_decision,
                    observation_status="error",
                    error=str(exc),
                )
            elapsed_seconds = time.monotonic() - started_at
            result_text = str(raw_result or "")
            timeout_metadata = self._build_timeout_metadata(
                status="not_configured" if timeout_seconds is None else (
                    "exceeded" if elapsed_seconds > timeout_seconds else "not_exceeded"
                ),
                timeout_seconds=timeout_seconds,
                elapsed_seconds=elapsed_seconds,
            )
            if timeout_metadata["status"] == "exceeded":
                return self._build_tool_execution_result(
                    status="timeout",
                    tool_name=normalized_tool_name,
                    args=tool_args,
                    result_text=result_text,
                    tool_spec=tool_spec,
                    schema_validation=schema_validation,
                    retry=self._build_retry_metadata(
                        status="recovered" if errors else "not_needed",
                        attempt_count=attempt,
                        max_attempts=max_attempts,
                        errors=errors,
                    ),
                    timeout=timeout_metadata,
                    policy_decision=policy_decision,
                    observation_status="timeout",
                    error="tool execution exceeded timeout_seconds",
                )
            return self._build_tool_execution_result(
                status="ok",
                tool_name=normalized_tool_name,
                args=tool_args,
                result_text=result_text,
                tool_spec=tool_spec,
                schema_validation=schema_validation,
                retry=self._build_retry_metadata(
                    status="recovered" if errors else "not_needed",
                    attempt_count=attempt,
                    max_attempts=max_attempts,
                    errors=errors,
                ),
                timeout=timeout_metadata,
                policy_decision=policy_decision,
                observation_status="ok",
            )
        return self._build_tool_execution_result(
            status="error",
            tool_name=normalized_tool_name,
            args=tool_args,
            result_text="",
            tool_spec=tool_spec,
            schema_validation=schema_validation,
            retry=self._build_retry_metadata(status="exhausted", attempt_count=max_attempts, max_attempts=max_attempts, errors=errors),
            timeout=self._build_timeout_metadata(status="not_configured", timeout_seconds=timeout_seconds, elapsed_seconds=0.0),
            policy_decision=policy_decision,
            observation_status="error",
            error="tool execution failed",
        )

    def evaluate_tool_policy(self, tool_name: str) -> Dict[str, Any]:
        normalized_tool_name = str(tool_name or "").strip()
        if not normalized_tool_name:
            return self._build_policy_decision(
                status="skipped",
                tool_name="",
                permission_level="unknown",
                reason_code="tool_name_required",
            )
        tool = self._get_registry_tool(normalized_tool_name)
        tool_spec = self._get_registry_tool_spec(normalized_tool_name)
        if tool is None:
            return self._build_policy_decision(
                status="skipped",
                tool_name=normalized_tool_name,
                permission_level="unknown",
                reason_code="tool_not_registered",
            )
        return self._evaluate_tool_policy(
            tool=tool,
            tool_spec=tool_spec,
            tool_name=normalized_tool_name,
        )

    def _list_framework_adapter_health(self) -> List[Dict[str, Any]]:
        method = getattr(self.framework_adapter_registry, "build_health_entries", None)
        if not callable(method):
            return []
        try:
            entries = method() or []
        except Exception as exc:
            return [{
                "adapter_id": "external_frameworks",
                "display_name": "External Framework Adapters",
                "adapter_type": "agent_framework",
                "status": "unavailable",
                "detail": str(exc),
            }]
        return [dict(item) for item in entries if isinstance(item, dict)]

    def _build_tool_entries(
        self,
        *,
        base_tools: List[Any],
        langchain_tools: List[Any],
        tool_specs: List[Any],
    ) -> List[Dict[str, Any]]:
        entries: Dict[str, Dict[str, Any]] = {}
        for tool in base_tools:
            name = str(getattr(tool, "name", "") or "").strip()
            if not name:
                continue
            entries[name] = {
                "name": name,
                "description": str(getattr(tool, "description", "") or ""),
                "kind": "base",
                "permission_level": self._permission_value(getattr(tool, "permission_level", "auto")),
                "has_schema": bool(getattr(tool, "parameters", None)),
                "tags": [],
            }
            entries[name]["risk_level"] = self._risk_level(
                permission_level=entries[name]["permission_level"],
                tags=[],
                name=name,
            )

        for tool in langchain_tools:
            name = str(getattr(tool, "name", "") or "").strip()
            if not name:
                continue
            entry = entries.setdefault(name, {"name": name})
            entry.update({
                "description": str(getattr(tool, "description", "") or entry.get("description", "")),
                "kind": "langchain" if entry.get("kind") != "base" else "base+langchain",
                "has_schema": bool(getattr(tool, "args_schema", None)) or entry.get("has_schema", False),
            })

        for spec in tool_specs:
            spec_data = spec.to_dict() if hasattr(spec, "to_dict") else dict(getattr(spec, "__dict__", {}) or {})
            name = str(spec_data.get("name") or "").strip()
            if not name:
                continue
            entry = entries.setdefault(name, {"name": name})
            permission_level = str(spec_data.get("permission_level") or entry.get("permission_level") or "auto")
            tags = list(spec_data.get("tags") or [])
            entry.update({
                "description": str(spec_data.get("description") or entry.get("description", "")),
                "kind": entry.get("kind") or "spec",
                "permission_level": permission_level,
                "render_mode": spec_data.get("render_mode"),
                "card_schema": spec_data.get("card_schema"),
                "deterministic": bool(spec_data.get("deterministic", False)),
                "supports_cache": bool(spec_data.get("supports_cache", False)),
                "tags": tags,
                "risk_level": self._risk_level(permission_level=permission_level, tags=tags, name=name),
            })

        for entry in entries.values():
            entry.setdefault("description", "")
            entry.setdefault("kind", "unknown")
            entry.setdefault("permission_level", "auto")
            entry.setdefault("risk_level", self._risk_level(
                permission_level=entry.get("permission_level", "auto"),
                tags=entry.get("tags", []),
                name=entry.get("name", ""),
            ))
            entry.setdefault("tags", [])
            entry.setdefault("has_schema", False)

        return sorted(entries.values(), key=lambda item: (item.get("risk_level") != "high", item.get("name", "")))

    def _list_mcp_capabilities(self) -> List[Dict[str, Any]]:
        try:
            catalog = self.mcp_registry_service.build_capability_catalog() or {}
        except Exception as exc:
            self._last_mcp_error = str(exc)
            return []
        capabilities = catalog.get("capabilities") if isinstance(catalog, dict) else []
        if not isinstance(capabilities, list):
            return []
        normalized = []
        for item in capabilities:
            if not isinstance(item, dict):
                continue
            capability = str(item.get("capability") or "").strip()
            if not capability:
                continue
            normalized.append({
                "capability": capability,
                "server_names": list(item.get("server_names") or []),
            })
        return sorted(normalized, key=lambda item: item["capability"])

    def _safe_list(self, target: Any, method_name: str) -> List[Any]:
        method = getattr(target, method_name, None)
        if not callable(method):
            return []
        try:
            value = method()
        except Exception as exc:
            self._last_registry_errors[method_name] = str(exc)
            return []
        return list(value or [])

    def _get_registry_tool(self, tool_name: str) -> Any:
        method = getattr(self.tool_registry, "get", None)
        if callable(method):
            try:
                return method(tool_name)
            except Exception:
                return None
        return None

    def _get_registry_tool_spec(self, tool_name: str) -> Any:
        method = getattr(self.tool_registry, "get_tool_spec", None)
        if callable(method):
            try:
                return method(tool_name)
            except Exception:
                return None
        return None

    def _validate_tool_args(self, tool: Any, args: Dict[str, Any]) -> Dict[str, Any]:
        parameters = getattr(tool, "parameters", None)
        missing_required: List[str] = []
        invalid_types: List[Dict[str, Any]] = []
        invalid_enum: List[Dict[str, Any]] = []
        if isinstance(parameters, dict):
            root_required = parameters.get("required")
            if isinstance(root_required, list):
                missing_required.extend(
                    str(item)
                    for item in root_required
                    if str(item or "").strip() and str(item) not in args
                )
            for name, metadata in parameters.items():
                if name == "required":
                    continue
                if not isinstance(metadata, dict):
                    continue
                if metadata.get("required") is True and name not in args:
                    missing_required.append(str(name))
                    continue
                if name not in args:
                    continue
                value = args.get(name)
                invalid_type = self._validate_schema_type(path=str(name), value=value, schema=metadata)
                if invalid_type is not None:
                    invalid_types.append(invalid_type)
                    continue
                enum_error = self._validate_schema_enum(path=str(name), value=value, schema=metadata)
                if enum_error is not None:
                    invalid_enum.append(enum_error)
                if metadata.get("type") == "object" and isinstance(value, dict):
                    missing_required.extend(self._validate_object_required(str(name), value, metadata))
        normalized_missing = sorted({item for item in missing_required if item})
        validation_status = "failed" if normalized_missing or invalid_types or invalid_enum else "passed"
        return {
            "status": validation_status,
            "missing_required": normalized_missing,
            "invalid_types": invalid_types,
            "invalid_enum": invalid_enum,
        }

    def _validate_schema_type(self, *, path: str, value: Any, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        expected = str(schema.get("type") or "").strip()
        if not expected:
            return None
        if self._value_matches_schema_type(value, expected):
            return None
        return {
            "path": path,
            "expected": expected,
            "actual": self._schema_type_name(value),
        }

    def _validate_schema_enum(self, *, path: str, value: Any, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = schema.get("enum")
        if not isinstance(allowed, list):
            return None
        if value in allowed:
            return None
        return {
            "path": path,
            "allowed": list(allowed),
            "actual": value,
        }

    def _validate_object_required(self, path: str, value: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        required = schema.get("required")
        if not isinstance(required, list):
            return []
        return [
            f"{path}.{item}"
            for item in required
            if str(item or "").strip() and str(item) not in value
        ]

    def _value_matches_schema_type(self, value: Any, expected: str) -> bool:
        if expected == "string":
            return isinstance(value, str)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        return True

    def _schema_type_name(self, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "array"
        if value is None:
            return "null"
        return type(value).__name__

    def _evaluate_tool_policy(self, *, tool: Any, tool_spec: Any, tool_name: str) -> Dict[str, Any]:
        permission_level = self._permission_level_for_execution(tool=tool, tool_spec=tool_spec)
        normalized_permission = str(permission_level or "auto").strip().lower()
        if normalized_permission in {"deny", "denied"}:
            return self._build_policy_decision(
                status="denied",
                tool_name=tool_name,
                permission_level=permission_level,
                reason_code="permission_level_denied",
                reason="registered tool permission_level denies execution",
            )
        if normalized_permission in {"ask", "high_risk"}:
            return self._build_policy_decision(
                status="approval_required",
                tool_name=tool_name,
                permission_level=permission_level,
                reason_code="permission_level_requires_approval",
                reason="registered tool permission_level requires approval before execution",
            )
        return self._build_policy_decision(
            status="allowed",
            tool_name=tool_name,
            permission_level=permission_level,
            reason_code="permission_level_auto_allowed",
            reason="registered tool permission_level allows execution",
        )

    def _permission_level_for_execution(self, *, tool: Any, tool_spec: Any) -> str:
        spec_data = self._tool_spec_data(tool_spec)
        if spec_data.get("permission_level"):
            return str(spec_data.get("permission_level") or "auto")
        return self._permission_value(getattr(tool, "permission_level", "auto"))

    def _build_policy_decision(
        self,
        *,
        status: str,
        tool_name: str,
        permission_level: str,
        reason_code: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        normalized_status = str(status or "allowed").strip().lower()
        return {
            "status": normalized_status,
            "allowed": normalized_status == "allowed",
            "requires_approval": normalized_status == "approval_required",
            "tool_name": str(tool_name or ""),
            "permission_level": str(permission_level or "auto"),
            "reason": str(reason or ""),
            "reason_code": str(reason_code or ""),
            "policy": "permission_level_gate_v1",
        }

    def _invoke_tool(self, tool: Any, args: Dict[str, Any]) -> Any:
        invoke = getattr(tool, "invoke", None)
        if callable(invoke):
            return self._resolve_maybe_async(invoke(args))
        func = getattr(tool, "func", None)
        if callable(func):
            return self._resolve_maybe_async(func(**args))
        raise RuntimeError(f"tool `{getattr(tool, 'name', 'unknown')}` is not executable")

    def _resolve_maybe_async(self, value: Any) -> Any:
        if not inspect.isawaitable(value):
            return value
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(value)
        raise RuntimeError("async tool execution requires an async runtime adapter")

    def _normalize_max_attempts(self, value: Any) -> int:
        try:
            attempts = int(value or 1)
        except (TypeError, ValueError):
            attempts = 1
        return max(1, attempts)

    def _resolve_timeout_seconds(self, value: Any, tool_spec: Any = None) -> Optional[float]:
        timeout_value = value
        if timeout_value is None and tool_spec is not None:
            timeout_value = getattr(tool_spec, "timeout_seconds", None)
        try:
            timeout = float(timeout_value)
        except (TypeError, ValueError):
            return None
        if timeout <= 0:
            return None
        return timeout

    def _build_retry_metadata(
        self,
        *,
        status: str,
        attempt_count: int,
        max_attempts: int,
        errors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "status": str(status or "not_needed"),
            "attempt_count": int(attempt_count or 0),
            "max_attempts": int(max_attempts or 0),
            "errors": list(errors or []),
        }

    def _normalize_policy_override(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        normalized = {
            "status": str(value.get("status") or "").strip().lower(),
            "approval_request_id": str(value.get("approval_request_id") or "").strip(),
            "source": str(value.get("source") or "").strip(),
        }
        return {
            key: item
            for key, item in normalized.items()
            if item
        }

    def _build_approved_policy_decision(
        self,
        *,
        original_decision: Dict[str, Any],
        override: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            **dict(original_decision),
            "status": "allowed",
            "allowed": True,
            "requires_approval": False,
            "reason": "approved tool continuation allows execution",
            "reason_code": "approved_tool_continuation",
            "original_status": str(original_decision.get("status") or "").strip(),
            "original_reason_code": str(original_decision.get("reason_code") or "").strip(),
            "override": dict(override),
        }

    def _build_timeout_metadata(
        self,
        *,
        status: str,
        timeout_seconds: Optional[float],
        elapsed_seconds: float,
    ) -> Dict[str, Any]:
        return {
            "status": str(status or "not_configured"),
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": elapsed_seconds,
            "enforcement": "post_call_elapsed_check",
        }

    def _build_tool_execution_result(
        self,
        *,
        status: str,
        tool_name: str,
        args: Dict[str, Any],
        result_text: str,
        tool_spec: Any = None,
        schema_validation: Optional[Dict[str, Any]] = None,
        retry: Optional[Dict[str, Any]] = None,
        timeout: Optional[Dict[str, Any]] = None,
        policy_decision: Optional[Dict[str, Any]] = None,
        observation_status: str = "ok",
        error: str = "",
    ) -> Dict[str, Any]:
        spec_data = self._tool_spec_data(tool_spec)
        action = {
            "type": "tool_action",
            "tool_name": str(tool_name or ""),
            "args": dict(args or {}),
        }
        observation = {
            "type": "tool_observation",
            "status": observation_status,
            "tool_name": str(tool_name or ""),
            "result_text": str(result_text or ""),
        }
        if error:
            observation["error"] = str(error)
        return {
            "contract_version": "phase-ii-tool-runtime-execution-v1",
            "status": str(status or "error"),
            "tool_name": str(tool_name or ""),
            "args": dict(args or {}),
            "result_text": str(result_text or ""),
            "execution": {
                "executor": "tool_runtime_service",
                "action": action,
                "observation": observation,
                "tool_spec": spec_data,
                "schema_validation": dict(schema_validation or {"status": "skipped", "missing_required": []}),
                "retry": dict(retry or self._build_retry_metadata(status="not_needed", attempt_count=1, max_attempts=1)),
                "timeout": dict(timeout or self._build_timeout_metadata(status="not_configured", timeout_seconds=None, elapsed_seconds=0.0)),
                "policy_decision": dict(policy_decision or self._build_policy_decision(
                    status="skipped",
                    tool_name=tool_name,
                    permission_level=str(spec_data.get("permission_level") or "unknown"),
                    reason_code="policy_not_evaluated",
                )),
            },
        }

    def _tool_spec_data(self, tool_spec: Any) -> Dict[str, Any]:
        if tool_spec is None:
            return {}
        if hasattr(tool_spec, "to_dict"):
            return dict(tool_spec.to_dict() or {})
        if isinstance(tool_spec, dict):
            return dict(tool_spec)
        return dict(getattr(tool_spec, "__dict__", {}) or {})

    def _permission_value(self, value: Any) -> str:
        return str(getattr(value, "value", value) or "auto")

    def _risk_level(self, *, permission_level: str, tags: Iterable[str], name: str) -> str:
        normalized_permission = str(permission_level or "").lower()
        normalized_tags = {str(item or "").lower() for item in tags}
        normalized_name = str(name or "").lower()
        if normalized_permission in {"deny", "ask", "high_risk"}:
            return "high"
        if "high_risk" in normalized_tags or ("write" in normalized_name and "filesystem" in normalized_name):
            return "high"
        return "normal"


_tool_runtime_service: Optional[ToolRuntimeService] = None


def get_tool_runtime_service() -> ToolRuntimeService:
    global _tool_runtime_service
    if _tool_runtime_service is None:
        _tool_runtime_service = ToolRuntimeService()
    return _tool_runtime_service
