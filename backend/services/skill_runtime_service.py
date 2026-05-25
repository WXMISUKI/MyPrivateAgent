"""Runtime skill discovery, matching, and prompt injection helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Dict, List, Optional


TOKEN_SPLIT_RE = re.compile(r"[\s,;:|/\\()\[\]{}<>._\-]+")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


@dataclass
class RuntimeSkillMatch:
    """A selected runtime skill with scoring and governance metadata."""

    skill_id: int
    name: str
    description: str = ""
    score: int = 0
    match_reasons: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    agent_roles: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    priority: int = 0
    activation_mode: str = "auto"
    domain: str = ""
    content_excerpt: str = ""
    storage_path: str = ""


@dataclass(frozen=True)
class SkillDefinition:
    """Stable runtime contract for a skill that can be audited and explained."""

    skill_id: int
    name: str
    version: str = "1.0.0"
    scope: str = "chat"
    trigger_rules: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    model_preferences: List[str] = field(default_factory=list)
    selection_reason: str = ""
    description: str = ""
    domain: str = ""
    agent_roles: List[str] = field(default_factory=list)
    activation_mode: str = "auto"
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "scope": self.scope,
            "trigger_rules": list(self.trigger_rules),
            "required_capabilities": list(self.required_capabilities),
            "allowed_tools": list(self.allowed_tools),
            "model_preferences": list(self.model_preferences),
            "selection_reason": self.selection_reason,
            "description": self.description,
            "domain": self.domain,
            "agent_roles": list(self.agent_roles),
            "activation_mode": self.activation_mode,
            "priority": self.priority,
        }


@dataclass
class RuntimeSkillContext:
    """Structured runtime skill payload injected into the agent loop."""

    system_prompt: str = ""
    selected_skills: List[RuntimeSkillMatch] = field(default_factory=list)
    skipped_skills: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.system_prompt.strip()


class SkillRuntimeService:
    """Load enabled skills and select deterministic runtime matches for one run."""

    def __init__(self, session_factory: Any = None, *, max_skills: int = 3, excerpt_chars: int = 800):
        self._session_factory = session_factory
        self.max_skills = max_skills
        self.excerpt_chars = excerpt_chars

    def get_runtime_context(
        self,
        *,
        user_message: str,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> RuntimeSkillContext:
        db = self._create_session()
        skills: List[Any] = []
        if db is not None:
            try:
                skills = self._load_enabled_skills(db)
            finally:
                db.close()
        return self.build_runtime_context(
            skills=skills,
            user_message=user_message,
            execution_context=execution_context or {},
        )

    def _create_session(self):
        if self._session_factory is not None:
            return self._session_factory()

        try:
            from database import SessionLocal
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.database import SessionLocal

        return SessionLocal()

    def _load_enabled_skills(self, db: Any) -> List[Any]:
        try:
            from models import Skill
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import Skill

        return (
            db.query(Skill)
            .filter(Skill.is_enabled == 1)
            .order_by(Skill.updated_at.desc(), Skill.id.desc())
            .all()
        )

    @staticmethod
    def _safe_text(value: Any) -> str:
        return str(value or "").strip()

    @classmethod
    def _tokenize(cls, value: str) -> List[str]:
        tokens = []
        for token in TOKEN_SPLIT_RE.split(cls._safe_text(value).lower()):
            normalized = token.strip()
            if len(normalized) >= 2:
                tokens.append(normalized)
        return tokens

    @staticmethod
    def _coerce_list(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [part.strip() for part in re.split(r"[;,|]", value) if part.strip()]
        return []

    @classmethod
    def _parse_frontmatter(cls, content: str) -> tuple[Dict[str, Any], str]:
        raw = str(content or "")
        match = FRONTMATTER_RE.match(raw)
        if not match:
            return {}, raw

        frontmatter: Dict[str, Any] = {}
        frontmatter_text, body = match.groups()
        pending_key: Optional[str] = None
        pending_items: List[str] = []

        def flush_pending() -> None:
            nonlocal pending_key, pending_items
            if pending_key is not None:
                frontmatter[pending_key] = list(pending_items)
            pending_key = None
            pending_items = []

        for raw_line in frontmatter_text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                continue
            if pending_key is not None and stripped.startswith("- "):
                pending_items.append(stripped[2:].strip())
                continue
            if ":" not in stripped:
                continue
            flush_pending()
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                frontmatter[key] = value
            else:
                pending_key = key
                pending_items = []
        flush_pending()
        return frontmatter, body

    @classmethod
    def _load_skill_payload(cls, skill: Any) -> Dict[str, Any]:
        storage_path = Path(str(getattr(skill, "storage_path", "") or "").strip())
        skill_md = storage_path / "SKILL.md"
        if not storage_path or not skill_md.exists():
            return {
                "content": "",
                "body": "",
                "tags": [],
                "triggers": [],
                "agent_roles": [],
                "required_capabilities": [],
                "usage": "",
                "notes": "",
                "description": cls._safe_text(getattr(skill, "description", "")),
            }

        content = skill_md.read_text(encoding="utf-8")
        frontmatter, body = cls._parse_frontmatter(content)
        return {
            "content": content,
            "body": body.strip(),
            "tags": cls._coerce_list(frontmatter.get("tags")),
            "triggers": cls._coerce_list(frontmatter.get("triggers")),
            "agent_roles": [value.lower() for value in cls._coerce_list(frontmatter.get("agent_roles") or frontmatter.get("roles"))],
            "required_capabilities": cls._coerce_list(frontmatter.get("required_capabilities") or frontmatter.get("capabilities")),
            "allowed_tools": cls._coerce_list(frontmatter.get("allowed_tools") or frontmatter.get("tools")),
            "model_preferences": cls._coerce_list(frontmatter.get("model_preferences") or frontmatter.get("models")),
            "version": cls._safe_text(frontmatter.get("version")) or "1.0.0",
            "priority": cls._coerce_priority(frontmatter.get("priority")),
            "activation_mode": cls._coerce_activation_mode(frontmatter.get("activation") or frontmatter.get("activation_mode")),
            "domain": cls._safe_text(frontmatter.get("domain")),
            "usage": cls._safe_text(frontmatter.get("usage")),
            "notes": cls._safe_text(frontmatter.get("notes")),
            "description": cls._safe_text(frontmatter.get("description") or getattr(skill, "description", "")),
        }

    @classmethod
    def _coerce_priority(cls, value: Any) -> int:
        try:
            return max(-10, min(10, int(str(value or "0").strip())))
        except (TypeError, ValueError):
            normalized = cls._safe_text(value).lower()
            mapping = {
                "critical": 8,
                "high": 5,
                "medium": 3,
                "low": 1,
            }
            return mapping.get(normalized, 0)

    @classmethod
    def _coerce_activation_mode(cls, value: Any) -> str:
        normalized = cls._safe_text(value).lower()
        if normalized in {"manual", "role_only", "always"}:
            return normalized
        return "auto"

    def _score_skill(
        self,
        *,
        skill: Any,
        payload: Dict[str, Any],
        user_message: str,
        execution_context: Dict[str, Any],
    ) -> tuple[int, List[str]]:
        score = 0
        reasons: List[str] = []

        role = self._safe_text(execution_context.get("agent_role")).lower()
        required_capabilities = [
            self._safe_text(value).lower()
            for value in (execution_context.get("required_capabilities") or [])
            if self._safe_text(value)
        ]

        activation_mode = payload.get("activation_mode", "auto")
        if activation_mode == "manual":
            reasons.append("activation:manual")
            return 0, reasons

        body = payload.get("body", "")
        searchable = " ".join(
            part
            for part in [
                self._safe_text(getattr(skill, "name", "")),
                payload.get("description", ""),
                " ".join(payload.get("tags", [])),
                " ".join(payload.get("triggers", [])),
                body[:800],
            ]
            if self._safe_text(part)
        ).lower()

        message_tokens = set(self._tokenize(user_message))
        searchable_tokens = set(self._tokenize(searchable))
        overlap = sorted(message_tokens & searchable_tokens)
        if overlap:
            overlap_score = min(4, len(overlap))
            score += overlap_score
            reasons.append(f"message_overlap:{','.join(overlap[:3])}")

        if role and role in payload.get("agent_roles", []):
            score += 3
            reasons.append(f"agent_role:{role}")
        elif activation_mode == "role_only" and payload.get("agent_roles"):
            reasons.append("activation:role_only_mismatch")
            return 0, reasons

        capability_hits = [cap for cap in required_capabilities if cap in [item.lower() for item in payload.get("required_capabilities", [])]]
        if capability_hits:
            score += min(3, len(capability_hits))
            reasons.append(f"capabilities:{','.join(capability_hits[:3])}")

        skill_name = self._safe_text(getattr(skill, "name", "")).lower()
        if skill_name and skill_name in self._safe_text(user_message).lower():
            score += 2
            reasons.append(f"direct_name:{skill_name}")

        for trigger in payload.get("triggers", []):
            normalized = trigger.lower()
            if normalized and normalized in self._safe_text(user_message).lower():
                score += 2
                reasons.append(f"trigger:{normalized}")

        priority = int(payload.get("priority") or 0)
        if priority:
            score += priority
            reasons.append(f"priority:{priority}")

        return score, reasons

    @staticmethod
    def _conflict_key(item: RuntimeSkillMatch) -> str:
        if item.domain:
            return item.domain.lower()
        if item.agent_roles:
            return "|".join(sorted(item.agent_roles))
        return item.name.lower()

    def _resolve_conflicts(
        self,
        *,
        candidates: List[RuntimeSkillMatch],
        skipped: List[Dict[str, Any]],
    ) -> List[RuntimeSkillMatch]:
        selected: List[RuntimeSkillMatch] = []
        by_conflict_key: Dict[str, RuntimeSkillMatch] = {}

        for item in candidates:
            conflict_key = self._conflict_key(item)
            existing = by_conflict_key.get(conflict_key)
            if existing is None:
                by_conflict_key[conflict_key] = item
                selected.append(item)
                continue

            winner = existing
            loser = item
            if (item.score, item.priority, -item.skill_id) > (existing.score, existing.priority, -existing.skill_id):
                winner = item
                loser = existing
                by_conflict_key[conflict_key] = item
                selected = [row for row in selected if row.skill_id != existing.skill_id]
                selected.append(item)

            skipped.append({
                "id": loser.skill_id,
                "name": loser.name,
                "reason": "conflict_suppressed",
                "conflict_key": conflict_key,
                "kept": winner.name,
            })

        selected.sort(key=lambda item: (-item.score, -item.priority, item.name.lower(), item.skill_id))
        return selected

    def build_runtime_context(
        self,
        *,
        skills: List[Any],
        user_message: str,
        execution_context: Dict[str, Any],
    ) -> RuntimeSkillContext:
        selected: List[RuntimeSkillMatch] = []
        skipped: List[Dict[str, Any]] = []

        for skill in skills:
            payload = self._load_skill_payload(skill)
            score, reasons = self._score_skill(
                skill=skill,
                payload=payload,
                user_message=user_message,
                execution_context=execution_context,
            )
            if score <= 0:
                skipped.append({
                    "id": getattr(skill, "id", None),
                    "name": self._safe_text(getattr(skill, "name", "")),
                    "reason": "no_runtime_match",
                })
                continue

            excerpt = self._safe_text(payload.get("body") or payload.get("content"))[: self.excerpt_chars]
            selected.append(
                RuntimeSkillMatch(
                    skill_id=int(getattr(skill, "id")),
                    name=self._safe_text(getattr(skill, "name", "")),
                    description=payload.get("description", ""),
                    score=score,
                    match_reasons=reasons,
                    tags=list(payload.get("tags", [])),
                    triggers=list(payload.get("triggers", [])),
                    agent_roles=list(payload.get("agent_roles", [])),
                    required_capabilities=list(payload.get("required_capabilities", [])),
                    priority=int(payload.get("priority") or 0),
                    activation_mode=self._safe_text(payload.get("activation_mode") or "auto") or "auto",
                    domain=self._safe_text(payload.get("domain")),
                    content_excerpt=excerpt,
                    storage_path=self._safe_text(getattr(skill, "storage_path", "")),
                )
            )

        selected = self._resolve_conflicts(candidates=selected, skipped=skipped)
        selected = selected[: self.max_skills]

        sections: List[str] = []
        if selected:
            sections.append("请将以下运行时 Skills 作为当前任务的可执行约束与参考，不要无关地罗列它们。")
            for item in selected:
                headline = f"- [skill:{item.name}]"
                if item.description:
                    headline += f" {item.description}"
                if item.match_reasons:
                    headline += f" (match={'; '.join(item.match_reasons)})"
                sections.append(headline)
                if item.content_excerpt:
                    sections.append(item.content_excerpt)

        return RuntimeSkillContext(
            system_prompt="\n".join(section for section in sections if section.strip()).strip(),
            selected_skills=selected,
            skipped_skills=skipped,
            metadata={
                "source": "skill_runtime_service",
                "scope": "chat",
                "selected_items": [
                    {
                        "type": "skill",
                        "id": item.skill_id,
                        "name": item.name,
                        "score": item.score,
                        "priority": item.priority,
                        "activation_mode": item.activation_mode,
                        "domain": item.domain,
                        "match_reasons": list(item.match_reasons),
                    }
                    for item in selected
                ],
                "skill_definitions": [
                    self._build_skill_definition_from_match(item).to_dict()
                    for item in selected
                ],
                "skipped_items": skipped,
                "selected_skill_ids": [item.skill_id for item in selected],
                "selected_skill_names": [item.name for item in selected],
                "selected_count": len(selected),
                "user_message": self._safe_text(user_message)[:200],
                "agent_role": self._safe_text(execution_context.get("agent_role")),
            },
        )

    def build_runtime_contract(self) -> Dict[str, Any]:
        db = self._create_session()
        skills: List[Any] = []
        if db is not None:
            try:
                skills = self._load_enabled_skills(db)
            finally:
                db.close()

        definitions = [
            self._build_skill_definition_from_skill(skill).to_dict()
            for skill in skills
        ]
        return {
            "contract_version": "phase-b-skill-definition-v1",
            "total_definitions": len(definitions),
            "definitions": definitions,
        }

    def _build_skill_definition_from_skill(self, skill: Any) -> SkillDefinition:
        payload = self._load_skill_payload(skill)
        return SkillDefinition(
            skill_id=int(getattr(skill, "id")),
            name=self._safe_text(getattr(skill, "name", "")),
            version=payload.get("version") or "1.0.0",
            scope="chat",
            trigger_rules=list(payload.get("triggers", [])),
            required_capabilities=list(payload.get("required_capabilities", [])),
            allowed_tools=list(payload.get("allowed_tools", [])),
            model_preferences=list(payload.get("model_preferences", [])),
            selection_reason="registered_enabled_skill",
            description=payload.get("description", ""),
            domain=self._safe_text(payload.get("domain")),
            agent_roles=list(payload.get("agent_roles", [])),
            activation_mode=self._safe_text(payload.get("activation_mode") or "auto") or "auto",
            priority=int(payload.get("priority") or 0),
        )

    def _build_skill_definition_from_match(self, item: RuntimeSkillMatch) -> SkillDefinition:
        return SkillDefinition(
            skill_id=item.skill_id,
            name=item.name,
            scope="chat",
            trigger_rules=list(item.triggers),
            required_capabilities=list(item.required_capabilities),
            selection_reason="; ".join(item.match_reasons),
            description=item.description,
            domain=item.domain,
            agent_roles=list(item.agent_roles),
            activation_mode=item.activation_mode,
            priority=item.priority,
        )


_skill_runtime_service: Optional[SkillRuntimeService] = None


def get_skill_runtime_service() -> SkillRuntimeService:
    global _skill_runtime_service
    if _skill_runtime_service is None:
        _skill_runtime_service = SkillRuntimeService()
    return _skill_runtime_service
