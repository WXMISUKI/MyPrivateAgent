"""Adapters that let the current app depend on framework interfaces."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .artifacts import Artifact, ArtifactStore
from .context import ContextStore, ConversationContext
from .memory import SessionRecord, SessionStore
from .providers import ModelProvider


class ModelRouterProviderAdapter(ModelProvider):
    """Wrap the current ModelRouter behind the framework provider interface."""

    def __init__(self, router: Any):
        self._router = router

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        return self._router.get_model(model_name, purpose=purpose)

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return self._router.get_model_config(model_name)


class ContextWindowAdapter(ConversationContext):
    """Wrap the current ContextWindow implementation."""

    def __init__(self, context_window: Any):
        self._context_window = context_window

    def add_user_message(self, content: str) -> Any:
        return self._context_window.add_user_message(content)

    def add_assistant_message(self, content: str) -> Any:
        return self._context_window.add_assistant_message(content)

    def add_system_message(self, content: str) -> Any:
        return self._context_window.add_system_message(content)

    def get_messages(self) -> List[Dict[str, str]]:
        return self._context_window.get_messages()

    def get_stats(self) -> Dict[str, Any]:
        return self._context_window.get_stats()

    def clear(self) -> None:
        self._context_window.clear()

    def is_empty(self) -> bool:
        return self._context_window.is_empty()

    @property
    def raw(self) -> Any:
        return self._context_window


class ContextManagerAdapter(ContextStore):
    """Wrap the current ContextManager implementation."""

    def __init__(self, manager: Any):
        self._manager = manager

    def get_context(self, conversation_id: int, model_name: Optional[str] = None) -> ContextWindowAdapter:
        return ContextWindowAdapter(self._manager.get_context(conversation_id, model_name))

    def delete_context(self, conversation_id: int) -> None:
        self._manager.delete_context(conversation_id)

    def get_stats(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        return self._manager.get_stats(conversation_id)


class MemoryManagerAdapter(SessionStore):
    """Wrap the current MemoryManager implementation."""

    def __init__(self, manager: Any):
        self._manager = manager

    def create_session(self, conversation_id: int, user_id: Optional[int] = None, model_name: Optional[str] = None) -> SessionRecord:
        session = self._manager.create_session(conversation_id, user_id=user_id, model_name=model_name)
        return self._to_record(session)

    def get_session(self, conversation_id: int) -> Optional[SessionRecord]:
        session = self._manager.get_session(conversation_id)
        return self._to_record(session) if session else None

    def update_session_activity(self, conversation_id: int) -> None:
        self._manager.update_session_activity(conversation_id)

    def increment_message_count(self, conversation_id: int) -> None:
        self._manager.increment_message_count(conversation_id)

    def update_tokens(self, conversation_id: int, tokens: int) -> None:
        self._manager.update_tokens(conversation_id, tokens)

    def get_stats(self) -> Dict[str, Any]:
        return self._manager.get_stats()

    def _to_record(self, session: Any) -> SessionRecord:
        return SessionRecord(
            conversation_id=session.conversation_id,
            state=session.state.value if hasattr(session.state, "value") else str(session.state),
            created_at=session.created_at,
            last_active=session.last_active,
            message_count=session.message_count,
            total_tokens=session.total_tokens,
            user_id=session.user_id,
            model_name=session.model_name,
            metadata=dict(session.metadata),
        )


class InMemoryArtifactStore(ArtifactStore):
    """Simple artifact store used until a persistent store is introduced."""

    def __init__(self):
        self._artifacts: List[Artifact] = []

    def create_artifact(
        self,
        *,
        conversation_id: Optional[int],
        kind: str,
        content: str,
        render_mode: Optional[str] = None,
        card_schema: Optional[str] = None,
        card: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        artifact = Artifact(
            artifact_id=f"artifact_{uuid4().hex}",
            conversation_id=conversation_id,
            kind=kind,
            content=content,
            created_at=datetime.now(),
            render_mode=render_mode,
            card_schema=card_schema,
            card=card,
            metadata=metadata or {},
        )
        self._artifacts.append(artifact)
        return artifact

    def list_artifacts(self, conversation_id: Optional[int] = None, kind: Optional[str] = None) -> List[Artifact]:
        results = self._artifacts
        if conversation_id is not None:
            results = [item for item in results if item.conversation_id == conversation_id]
        if kind is not None:
            results = [item for item in results if item.kind == kind]
        return list(results)


class SQLAlchemyArtifactStore(ArtifactStore):
    """Database-backed artifact store for runtime replay and audit."""

    def __init__(self, session_factory: Any):
        self._session_factory = session_factory

    def create_artifact(
        self,
        *,
        conversation_id: Optional[int],
        kind: str,
        content: str,
        render_mode: Optional[str] = None,
        card_schema: Optional[str] = None,
        card: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        try:
            from models import ArtifactRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import ArtifactRecord

        artifact = Artifact(
            artifact_id=f"artifact_{uuid4().hex}",
            conversation_id=conversation_id,
            kind=kind,
            content=content,
            created_at=datetime.now(),
            render_mode=render_mode,
            card_schema=card_schema,
            card=card,
            metadata=metadata or {},
        )

        db = self._session_factory()
        try:
            record = ArtifactRecord(
                artifact_id=artifact.artifact_id,
                conversation_id=artifact.conversation_id,
                kind=artifact.kind,
                content=artifact.content,
                render_mode=artifact.render_mode,
                card_schema=artifact.card_schema,
                card=artifact.card,
                artifact_metadata=artifact.metadata,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            artifact.created_at = record.created_at or artifact.created_at
            return artifact
        finally:
            db.close()

    def list_artifacts(self, conversation_id: Optional[int] = None, kind: Optional[str] = None) -> List[Artifact]:
        try:
            from models import ArtifactRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import ArtifactRecord

        db = self._session_factory()
        try:
            query = db.query(ArtifactRecord)
            if conversation_id is not None:
                query = query.filter(ArtifactRecord.conversation_id == conversation_id)
            if kind is not None:
                query = query.filter(ArtifactRecord.kind == kind)
            records = query.order_by(ArtifactRecord.created_at.asc()).all()
            return [
                Artifact(
                    artifact_id=record.artifact_id,
                    conversation_id=record.conversation_id,
                    kind=record.kind,
                    content=record.content,
                    created_at=record.created_at,
                    render_mode=record.render_mode,
                    card_schema=record.card_schema,
                    card=record.card,
                    metadata=dict(record.artifact_metadata or {}),
                )
                for record in records
            ]
        finally:
            db.close()


_provider_adapter: Optional[ModelRouterProviderAdapter] = None
_context_store_adapter: Optional[ContextManagerAdapter] = None
_memory_store_adapter: Optional[MemoryManagerAdapter] = None
_artifact_store: Optional[InMemoryArtifactStore] = None


def get_model_provider() -> ModelProvider:
    """Return the framework-facing provider adapter."""
    global _provider_adapter
    if _provider_adapter is None:
        try:
            from model_router import get_model_router
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.model_router import get_model_router

        _provider_adapter = ModelRouterProviderAdapter(get_model_router())
    return _provider_adapter


def get_context_store() -> ContextStore:
    """Return the framework-facing context store adapter."""
    global _context_store_adapter
    if _context_store_adapter is None:
        try:
            from harness.context_manager import get_context_manager
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.harness.context_manager import get_context_manager

        _context_store_adapter = ContextManagerAdapter(get_context_manager())
    return _context_store_adapter


def get_memory_store() -> SessionStore:
    """Return the framework-facing session store adapter."""
    global _memory_store_adapter
    if _memory_store_adapter is None:
        try:
            from harness.memory_manager import get_memory_manager
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.harness.memory_manager import get_memory_manager

        _memory_store_adapter = MemoryManagerAdapter(get_memory_manager())
    return _memory_store_adapter


def get_artifact_store() -> ArtifactStore:
    """Return the framework-facing artifact store."""
    global _artifact_store
    if _artifact_store is None:
        try:
            try:
                from database import SessionLocal
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                from backend.database import SessionLocal

            _artifact_store = SQLAlchemyArtifactStore(SessionLocal)
        except Exception:  # pragma: no cover - keep runtime usable in non-db tests
            _artifact_store = InMemoryArtifactStore()
    return _artifact_store
