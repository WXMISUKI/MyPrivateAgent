"""Runtime knowledge injection built from reviewed learnings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


PRIORITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


@dataclass
class RuntimeKnowledgeContext:
    """Structured runtime knowledge injected into the agent loop."""

    system_prompt: str = ""
    prompt_keys: List[str] = field(default_factory=list)
    practice_ids: List[str] = field(default_factory=list)
    prompt_count: int = 0
    practice_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.system_prompt.strip()


class RuntimeKnowledgeLevel(str, Enum):
    """Governance levels for runtime knowledge injection."""

    DIAGNOSTIC = "diagnostic"
    ADVISORY = "advisory"
    ENFORCED = "enforced"


class RuntimeLearningService:
    """Loads approved knowledge and converts it into runtime guidance."""

    def __init__(self, session_factory: Any = None, *, max_practices: int = 5):
        self._session_factory = session_factory
        self.max_practices = max_practices

    def get_runtime_context(
        self,
        *,
        user_message: str = "",
        area: Optional[str] = None,
        scope: str = "chat",
    ) -> RuntimeKnowledgeContext:
        prompts: List[Any] = []
        practices: List[Any] = []

        db = self._create_session()
        if db is not None:
            try:
                prompts = self._load_active_prompts(db, area=area)
                practices = self._load_best_practices(db, limit=self.max_practices)
            finally:
                db.close()

        context = self.build_runtime_context(prompts=prompts, practices=practices, scope=scope)
        context.metadata["user_message"] = user_message[:200]
        if area:
            context.metadata["area"] = area
        return context

    @staticmethod
    def _normalize_tags(item: Any) -> List[str]:
        raw_tags = getattr(item, "tags", None) or []
        if not isinstance(raw_tags, list):
            return []
        return [str(tag).strip().lower() for tag in raw_tags if str(tag).strip()]

    @classmethod
    def _extract_scope(cls, tags: List[str], *, default: str = "global") -> str:
        for tag in tags:
            if tag.startswith("scope:"):
                return tag.split(":", 1)[1].strip() or default
        return default

    @classmethod
    def _is_disabled(cls, tags: List[str]) -> bool:
        return "disabled" in tags or "inactive" in tags

    @classmethod
    def _is_rollback(cls, tags: List[str]) -> bool:
        return "rollback" in tags or any(tag.startswith("rollback:") for tag in tags)

    @classmethod
    def _build_prompt_governance(cls, prompt: Any) -> Dict[str, Any]:
        tags = cls._normalize_tags(prompt)
        enabled = bool(getattr(prompt, "is_active", True)) and not cls._is_disabled(tags)
        return {
            "level": cls.classify_prompt(prompt).value,
            "scope": cls._extract_scope(tags),
            "enabled": enabled,
            "rollback": cls._is_rollback(tags),
            "tags": tags,
        }

    @classmethod
    def _build_practice_governance(cls, practice: Any) -> Dict[str, Any]:
        tags = cls._normalize_tags(practice)
        runtime_config = {}
        trade_offs = getattr(practice, "trade_offs", None)
        if isinstance(trade_offs, dict):
            runtime_value = trade_offs.get("runtime")
            if isinstance(runtime_value, dict):
                runtime_config = runtime_value

        enabled = bool(runtime_config.get("enabled", True)) and not cls._is_disabled(tags)
        scope = str(runtime_config.get("scope") or cls._extract_scope(tags)).strip() or "global"
        rollback = bool(runtime_config.get("rollback", False)) or cls._is_rollback(tags)
        rollback_reason = str(runtime_config.get("rollback_reason", "") or "").strip()
        return {
            "level": cls.classify_practice(practice).value,
            "scope": scope,
            "enabled": enabled,
            "rollback": rollback,
            "rollback_reason": rollback_reason,
            "tags": tags,
        }

    @classmethod
    def classify_prompt(cls, prompt: Any) -> RuntimeKnowledgeLevel:
        tags = cls._normalize_tags(prompt)
        prompt_type = str(getattr(prompt, "prompt_type", "") or "").strip().lower()
        priority = int(getattr(prompt, "priority", 0) or 0)

        if "diagnostic" in tags:
            return RuntimeKnowledgeLevel.DIAGNOSTIC
        if "enforced" in tags:
            return RuntimeKnowledgeLevel.ENFORCED
        if prompt_type in {"tool_usage", "workflow"} or priority >= 5:
            return RuntimeKnowledgeLevel.ENFORCED
        return RuntimeKnowledgeLevel.ADVISORY

    @classmethod
    def classify_practice(cls, practice: Any) -> RuntimeKnowledgeLevel:
        tags = cls._normalize_tags(practice)
        priority = PRIORITY_RANK.get(str(getattr(practice, "priority", "")).lower(), 0)

        if "diagnostic" in tags:
            return RuntimeKnowledgeLevel.DIAGNOSTIC
        if "enforced" in tags or priority >= PRIORITY_RANK["high"]:
            return RuntimeKnowledgeLevel.ENFORCED
        return RuntimeKnowledgeLevel.ADVISORY

    def _create_session(self):
        if self._session_factory is not None:
            return self._session_factory()

        try:
            from database import SessionLocal
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.database import SessionLocal

        return SessionLocal()

    def _load_active_prompts(self, db: Any, *, area: Optional[str] = None) -> List[Any]:
        try:
            from models import SystemPrompt
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import SystemPrompt

        query = db.query(SystemPrompt).filter(SystemPrompt.is_active == True)  # noqa: E712
        if area:
            query = query.filter((SystemPrompt.area == None) | (SystemPrompt.area == area))  # noqa: E711
        return query.order_by(SystemPrompt.priority.desc(), SystemPrompt.updated_at.desc()).all()

    def _load_best_practices(self, db: Any, *, limit: int) -> List[Any]:
        try:
            from models import BestPractice
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import BestPractice

        practices = db.query(BestPractice).order_by(BestPractice.updated_at.desc()).all()
        practices.sort(
            key=lambda item: (
                -PRIORITY_RANK.get(str(getattr(item, "priority", "")).lower(), 0),
                str(getattr(item, "updated_at", "") or ""),
            )
        )
        return practices[:limit]

    @staticmethod
    def build_runtime_context(*, prompts: List[Any], practices: List[Any], scope: str = "chat") -> RuntimeKnowledgeContext:
        sections: List[str] = []
        prompt_keys: List[str] = []
        practice_ids: List[str] = []
        governance: Dict[str, List[str]] = {
            RuntimeKnowledgeLevel.ENFORCED.value: [],
            RuntimeKnowledgeLevel.ADVISORY.value: [],
            RuntimeKnowledgeLevel.DIAGNOSTIC.value: [],
        }
        selected_items: List[Dict[str, Any]] = []
        skipped_items: List[Dict[str, Any]] = []

        enforced_lines: List[str] = []
        advisory_lines: List[str] = []

        if prompts:
            for prompt in prompts:
                prompt_key = str(getattr(prompt, "prompt_key", "") or "")
                prompt_type = str(getattr(prompt, "prompt_type", "") or "general")
                content = str(getattr(prompt, "content", "") or "").strip()
                if not content:
                    continue
                item_governance = RuntimeLearningService._build_prompt_governance(prompt)
                level = RuntimeKnowledgeLevel(item_governance["level"])
                prompt_keys.append(prompt_key)
                governance[level.value].append(f"prompt:{prompt_key}")
                item_scope = item_governance["scope"]
                item_ref = {
                    "type": "prompt",
                    "id": prompt_key,
                    "level": level.value,
                    "scope": item_scope,
                }

                if not item_governance["enabled"]:
                    skipped_items.append({**item_ref, "reason": "disabled"})
                    continue
                if item_governance["rollback"]:
                    skipped_items.append({**item_ref, "reason": "rollback"})
                    continue
                if level == RuntimeKnowledgeLevel.DIAGNOSTIC:
                    skipped_items.append({**item_ref, "reason": "diagnostic"})
                    continue
                if item_scope not in {"global", scope}:
                    skipped_items.append({**item_ref, "reason": "scope_mismatch"})
                    continue

                selected_items.append(item_ref)
                line = f"- [{prompt_type}:{prompt_key}] {content}"
                if level == RuntimeKnowledgeLevel.ENFORCED:
                    enforced_lines.append(line)
                elif level == RuntimeKnowledgeLevel.ADVISORY:
                    advisory_lines.append(line)

        if practices:
            for practice in practices:
                practice_id = str(getattr(practice, "practice_id", "") or "")
                title = str(getattr(practice, "title", "") or "").strip()
                description = str(getattr(practice, "description", "") or "").strip()
                if not title and not description:
                    continue
                item_governance = RuntimeLearningService._build_practice_governance(practice)
                level = RuntimeKnowledgeLevel(item_governance["level"])
                practice_ids.append(practice_id)
                governance[level.value].append(f"practice:{practice_id}")
                item_scope = item_governance["scope"]
                item_ref = {
                    "type": "practice",
                    "id": practice_id,
                    "level": level.value,
                    "scope": item_scope,
                }
                if not item_governance["enabled"]:
                    skipped_items.append({**item_ref, "reason": "disabled"})
                    continue
                if item_governance["rollback"]:
                    skipped_items.append({
                        **item_ref,
                        "reason": "rollback",
                        "rollback_reason": item_governance.get("rollback_reason"),
                    })
                    continue
                if level == RuntimeKnowledgeLevel.DIAGNOSTIC:
                    skipped_items.append({**item_ref, "reason": "diagnostic"})
                    continue
                if item_scope not in {"global", scope}:
                    skipped_items.append({**item_ref, "reason": "scope_mismatch"})
                    continue

                selected_items.append(item_ref)
                summary = title or "未命名最佳实践"
                if description:
                    summary = f"{summary}：{description}"
                line = f"- [{practice_id}] {summary}"
                if level == RuntimeKnowledgeLevel.ENFORCED:
                    enforced_lines.append(line)
                elif level == RuntimeKnowledgeLevel.ADVISORY:
                    advisory_lines.append(line)

        if enforced_lines:
            sections.append("请严格遵循以下运行时规则：")
            sections.extend(enforced_lines)
        if advisory_lines:
            sections.append("请优先参考以下运行时建议：")
            sections.extend(advisory_lines)

        system_prompt = "\n".join(sections).strip()
        return RuntimeKnowledgeContext(
            system_prompt=system_prompt,
            prompt_keys=prompt_keys,
            practice_ids=practice_ids,
            prompt_count=len(prompt_keys),
            practice_count=len(practice_ids),
            metadata={
                "prompt_keys": prompt_keys,
                "practice_ids": practice_ids,
                "prompt_count": len(prompt_keys),
                "practice_count": len(practice_ids),
                "scope": scope,
                "governance": governance,
                "enforced_count": len(governance[RuntimeKnowledgeLevel.ENFORCED.value]),
                "advisory_count": len(governance[RuntimeKnowledgeLevel.ADVISORY.value]),
                "diagnostic_count": len(governance[RuntimeKnowledgeLevel.DIAGNOSTIC.value]),
                "selected_items": selected_items,
                "skipped_items": skipped_items,
                "source": "runtime_learning_service",
            },
        )


_runtime_learning_service: Optional[RuntimeLearningService] = None


def get_runtime_learning_service() -> RuntimeLearningService:
    global _runtime_learning_service
    if _runtime_learning_service is None:
        _runtime_learning_service = RuntimeLearningService()
    return _runtime_learning_service
