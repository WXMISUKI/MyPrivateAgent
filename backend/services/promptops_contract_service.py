"""PromptOps compatibility read model for existing system prompts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


PROMPTOPS_CONTRACT_VERSION = "promptops-versioned-prompt-v1"
PROMPTOPS_REGISTRY_CONTRACT_VERSION = "promptops-registry-v1"

ALLOWED_STATUSES = {"draft", "review", "active", "archived"}
ALLOWED_APPROVAL_STATES = {"not_required", "pending", "approved", "rejected"}
TAG_FIELDS = {
    "version": "version",
    "status": "status",
    "owner": "owner",
    "grounding_policy": "grounding_policy_ref",
    "eval_set": "eval_set_ref",
    "approval": "approval_state",
    "rollout": "rollout_strategy",
    "rollback_target": "rollback_target",
}
VARIABLE_PATTERN = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*}}")


@dataclass(frozen=True)
class PromptOpsContractService:
    """Builds governance-visible PromptOps contracts without changing runtime injection."""

    def build_registry(self, prompts: Iterable[Any]) -> Dict[str, Any]:
        prompt_contracts = [self.normalize_prompt(prompt) for prompt in prompts]
        return {
            "contract_version": PROMPTOPS_REGISTRY_CONTRACT_VERSION,
            "promptops_contract_version": PROMPTOPS_CONTRACT_VERSION,
            "prompt_count": len(prompt_contracts),
            "active_prompt_count": sum(1 for prompt in prompt_contracts if prompt["status"] == "active"),
            "behavior_boundary": {
                "mode": "visibility_only",
                "chat_prompt_injection_changed": False,
                "activation_side_effects": False,
            },
            "prompts": prompt_contracts,
        }

    def normalize_prompt(self, prompt: Any) -> Dict[str, Any]:
        tags = self._normalize_tags(getattr(prompt, "tags", None))
        tag_values = self._extract_tag_values(tags)
        content = str(getattr(prompt, "content", "") or "")
        is_active = bool(getattr(prompt, "is_active", True))
        explicit_status = self._normalize_status(tag_values.get("status"))
        status = explicit_status or ("active" if is_active else "archived")
        version = self._normalize_version(tag_values.get("version"))
        approval_state = self._normalize_approval(tag_values.get("approval_state"))
        prompt_type = str(getattr(prompt, "prompt_type", "") or "general").strip() or "general"
        priority = int(getattr(prompt, "priority", 0) or 0)

        return {
            "contract_version": PROMPTOPS_CONTRACT_VERSION,
            "prompt_key": str(getattr(prompt, "prompt_key", "") or ""),
            "version": version,
            "status": status,
            "prompt_type": prompt_type,
            "template": content,
            "variables_schema": self._build_variables_schema(content),
            "owner": tag_values.get("owner"),
            "area": self._serialize_area(getattr(prompt, "area", None)),
            "tags": tags,
            "grounding_policy_ref": tag_values.get("grounding_policy_ref"),
            "eval_set_ref": tag_values.get("eval_set_ref"),
            "approval_state": approval_state,
            "rollout_strategy": tag_values.get("rollout_strategy"),
            "rollback_target": tag_values.get("rollback_target"),
            "runtime_binding": {
                "source": "system_prompts",
                "prompt_type": prompt_type,
                "priority": priority,
                "is_active": is_active,
                "injection_behavior": "unchanged",
            },
        }

    @staticmethod
    def _normalize_tags(raw_tags: Any) -> List[str]:
        if not isinstance(raw_tags, list):
            return []
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]

    @staticmethod
    def _extract_tag_values(tags: List[str]) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for tag in tags:
            if ":" not in tag:
                continue
            key, value = tag.split(":", 1)
            field = TAG_FIELDS.get(key.strip().lower())
            normalized_value = value.strip()
            if field and normalized_value:
                values[field] = normalized_value
        return values

    @staticmethod
    def _normalize_status(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized if normalized in ALLOWED_STATUSES else None

    @staticmethod
    def _normalize_approval(value: Optional[str]) -> str:
        if value is None:
            return "not_required"
        normalized = value.strip().lower()
        return normalized if normalized in ALLOWED_APPROVAL_STATES else "not_required"

    @staticmethod
    def _normalize_version(value: Optional[str]) -> str:
        normalized = str(value or "").strip()
        return normalized or "1"

    @staticmethod
    def _serialize_area(area: Any) -> Optional[str]:
        if area is None:
            return None
        return str(getattr(area, "value", area) or "").strip() or None

    @staticmethod
    def _build_variables_schema(template: str) -> Dict[str, Any]:
        variables = list(dict.fromkeys(VARIABLE_PATTERN.findall(template or "")))
        return {
            "type": "object",
            "properties": {
                variable: {"type": "string"}
                for variable in variables
            },
            "required": variables,
            "additionalProperties": True,
        }


_promptops_contract_service: Optional[PromptOpsContractService] = None


def get_promptops_contract_service() -> PromptOpsContractService:
    global _promptops_contract_service
    if _promptops_contract_service is None:
        _promptops_contract_service = PromptOpsContractService()
    return _promptops_contract_service
