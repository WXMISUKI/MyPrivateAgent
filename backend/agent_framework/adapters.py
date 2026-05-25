"""Adapters that let the current app depend on framework interfaces."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from config import DB_MODE, EMBEDDED_WORKSPACE_STORE_MODE
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import DB_MODE, EMBEDDED_WORKSPACE_STORE_MODE

from .artifacts import Artifact, ArtifactStore
from .context import ContextStore, ConversationContext
from .memory import SessionRecord, SessionStore
from .persistence import EmbeddedRunWorkspaceStore, InMemoryEmbeddedRunWorkspaceStore, build_embedded_workspace_state_contract
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


class SQLAlchemyEmbeddedRunWorkspaceStore(EmbeddedRunWorkspaceStore):
    """Database-backed persistence seam for Embedded SDK snapshots and descriptors."""

    def __init__(self, session_factory: Any, *, allow_operation_fallback: bool = True, backend_mode: str = "prefer_sql_with_fallback"):
        self._session_factory = session_factory
        self._fallback = InMemoryEmbeddedRunWorkspaceStore()
        self._fallback_active = False
        self._fallback_reason = ""
        self._last_error = ""
        self._allow_operation_fallback = bool(allow_operation_fallback)
        self._backend_mode = str(backend_mode or "prefer_sql_with_fallback").strip() or "prefer_sql_with_fallback"

    def describe_backend(self) -> Dict[str, Any]:
        return {
            "backend_kind": "sqlalchemy",
            "durable": True,
            "backend_mode": self._backend_mode,
            "operation_fallback_allowed": bool(self._allow_operation_fallback),
            "fallback_active": bool(self._fallback_active),
            "fallback_reason": str(self._fallback_reason or "").strip(),
            "last_error": str(self._last_error or "").strip(),
            "state_contract": build_embedded_workspace_state_contract(),
        }

    def save_run_snapshot(self, run_snapshot: Dict[str, Any]) -> None:
        try:
            from models import EmbeddedRunWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedRunWorkspaceRecord

        normalized_run_id = str((run_snapshot or {}).get("run_id") or "").strip()
        if not normalized_run_id:
            return
        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedRunWorkspaceRecord).filter(
                    EmbeddedRunWorkspaceRecord.run_id == normalized_run_id
                ).first()
                if record is None:
                    record = EmbeddedRunWorkspaceRecord(
                        run_id=normalized_run_id,
                        conversation_id=run_snapshot.get("conversation_id"),
                        parent_run_id=run_snapshot.get("parent_run_id"),
                        run_kind=run_snapshot.get("run_kind"),
                        state=run_snapshot.get("state"),
                        run_snapshot=dict(run_snapshot or {}),
                        events=[],
                        workspace_metadata=dict((run_snapshot or {}).get("metadata") or {}),
                    )
                    db.add(record)
                else:
                    record.conversation_id = run_snapshot.get("conversation_id")
                    record.parent_run_id = run_snapshot.get("parent_run_id")
                    record.run_kind = run_snapshot.get("run_kind")
                    record.state = run_snapshot.get("state")
                    record.run_snapshot = dict(run_snapshot or {})
                    record.workspace_metadata = dict((run_snapshot or {}).get("metadata") or {})
                db.commit()
                self._mark_backend_success()
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback("save_run_snapshot", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error("save_run_snapshot", exc)) from exc
            self._fallback.save_run_snapshot(run_snapshot)

    def get_run_snapshot(self, run_id: str) -> Optional[Dict[str, Any]]:
        try:
            from models import EmbeddedRunWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedRunWorkspaceRecord

        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedRunWorkspaceRecord).filter(
                    EmbeddedRunWorkspaceRecord.run_id == str(run_id or "").strip()
                ).first()
                self._mark_backend_success()
                return dict(record.run_snapshot or {}) if record is not None else None
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback("get_run_snapshot", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error("get_run_snapshot", exc)) from exc
            return self._fallback.get_run_snapshot(run_id)

    def save_events(self, run_id: str, events: List[Dict[str, Any]]) -> None:
        try:
            from models import EmbeddedRunWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedRunWorkspaceRecord

        normalized_run_id = str(run_id or "").strip()
        if not normalized_run_id:
            return
        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedRunWorkspaceRecord).filter(
                    EmbeddedRunWorkspaceRecord.run_id == normalized_run_id
                ).first()
                if record is None:
                    record = EmbeddedRunWorkspaceRecord(
                        run_id=normalized_run_id,
                        run_snapshot={"run_id": normalized_run_id},
                        events=[dict(event or {}) for event in list(events or [])],
                    )
                    db.add(record)
                else:
                    record.events = [dict(event or {}) for event in list(events or [])]
                db.commit()
                self._mark_backend_success()
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback("save_events", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error("save_events", exc)) from exc
            self._fallback.save_events(run_id, events)

    def get_events(self, run_id: str) -> List[Dict[str, Any]]:
        try:
            from models import EmbeddedRunWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedRunWorkspaceRecord

        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedRunWorkspaceRecord).filter(
                    EmbeddedRunWorkspaceRecord.run_id == str(run_id or "").strip()
                ).first()
                self._mark_backend_success()
                return [dict(event or {}) for event in list(record.events or [])] if record is not None else []
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback("get_events", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error("get_events", exc)) from exc
            return self._fallback.get_events(run_id)

    def save_approval_snapshot(self, approval_snapshot: Dict[str, Any]) -> None:
        try:
            from models import EmbeddedApprovalWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedApprovalWorkspaceRecord

        request_id = str((approval_snapshot or {}).get("request_id") or "").strip()
        if not request_id:
            return
        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedApprovalWorkspaceRecord).filter(
                    EmbeddedApprovalWorkspaceRecord.request_id == request_id
                ).first()
                if record is None:
                    record = EmbeddedApprovalWorkspaceRecord(
                        request_id=request_id,
                        run_id=approval_snapshot.get("run_id"),
                        approval_snapshot=dict(approval_snapshot or {}),
                    )
                    db.add(record)
                else:
                    record.run_id = approval_snapshot.get("run_id")
                    record.approval_snapshot = dict(approval_snapshot or {})
                db.commit()
                self._mark_backend_success()
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback("save_approval_snapshot", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error("save_approval_snapshot", exc)) from exc
            self._fallback.save_approval_snapshot(approval_snapshot)

    def get_approval_snapshot(self, request_id: str) -> Optional[Dict[str, Any]]:
        try:
            from models import EmbeddedApprovalWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedApprovalWorkspaceRecord

        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedApprovalWorkspaceRecord).filter(
                    EmbeddedApprovalWorkspaceRecord.request_id == str(request_id or "").strip()
                ).first()
                self._mark_backend_success()
                return dict(record.approval_snapshot or {}) if record is not None else None
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback("get_approval_snapshot", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error("get_approval_snapshot", exc)) from exc
            return self._fallback.get_approval_snapshot(request_id)

    def save_tool_continuation_descriptor(self, request_id: str, descriptor: Dict[str, Any]) -> None:
        self._save_continuation(
            continuation_key=str(request_id or "").strip(),
            continuation_kind="tool",
            run_id=None,
            request_id=request_id,
            descriptor=descriptor,
        )

    def get_tool_continuation_descriptor(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self._get_continuation(str(request_id or "").strip(), "tool")

    def delete_tool_continuation_descriptor(self, request_id: str) -> None:
        self._delete_continuation(str(request_id or "").strip(), "tool")

    def save_loop_continuation_descriptor(self, run_id: str, descriptor: Dict[str, Any]) -> None:
        self._save_continuation(
            continuation_key=str(run_id or "").strip(),
            continuation_kind="loop",
            run_id=run_id,
            request_id=(descriptor or {}).get("request_id"),
            descriptor=descriptor,
        )

    def get_loop_continuation_descriptor(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._get_continuation(str(run_id or "").strip(), "loop")

    def delete_loop_continuation_descriptor(self, run_id: str) -> None:
        self._delete_continuation(str(run_id or "").strip(), "loop")

    def _save_continuation(
        self,
        *,
        continuation_key: str,
        continuation_kind: str,
        run_id: Optional[str],
        request_id: Optional[str],
        descriptor: Dict[str, Any],
    ) -> None:
        try:
            from models import EmbeddedContinuationWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedContinuationWorkspaceRecord

        if not continuation_key:
            return
        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedContinuationWorkspaceRecord).filter(
                    EmbeddedContinuationWorkspaceRecord.continuation_key == continuation_key,
                    EmbeddedContinuationWorkspaceRecord.continuation_kind == continuation_kind,
                ).first()
                if record is None:
                    record = EmbeddedContinuationWorkspaceRecord(
                        continuation_key=continuation_key,
                        continuation_kind=continuation_kind,
                        run_id=run_id,
                        request_id=request_id,
                        descriptor=dict(descriptor or {}),
                    )
                    db.add(record)
                else:
                    record.run_id = run_id
                    record.request_id = request_id
                    record.descriptor = dict(descriptor or {})
                db.commit()
                self._mark_backend_success()
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback(f"save_{continuation_kind}_continuation", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error(f"save_{continuation_kind}_continuation", exc)) from exc
            if continuation_kind == "tool":
                self._fallback.save_tool_continuation_descriptor(continuation_key, descriptor)
            else:
                self._fallback.save_loop_continuation_descriptor(continuation_key, descriptor)

    def _get_continuation(self, continuation_key: str, continuation_kind: str) -> Optional[Dict[str, Any]]:
        try:
            from models import EmbeddedContinuationWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedContinuationWorkspaceRecord

        try:
            db = self._session_factory()
            try:
                record = db.query(EmbeddedContinuationWorkspaceRecord).filter(
                    EmbeddedContinuationWorkspaceRecord.continuation_key == continuation_key,
                    EmbeddedContinuationWorkspaceRecord.continuation_kind == continuation_kind,
                ).first()
                self._mark_backend_success()
                return dict(record.descriptor or {}) if record is not None else None
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback(f"get_{continuation_kind}_continuation", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error(f"get_{continuation_kind}_continuation", exc)) from exc
            return (
                self._fallback.get_tool_continuation_descriptor(continuation_key)
                if continuation_kind == "tool"
                else self._fallback.get_loop_continuation_descriptor(continuation_key)
            )

    def _delete_continuation(self, continuation_key: str, continuation_kind: str) -> None:
        try:
            from models import EmbeddedContinuationWorkspaceRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import EmbeddedContinuationWorkspaceRecord

        try:
            db = self._session_factory()
            try:
                db.query(EmbeddedContinuationWorkspaceRecord).filter(
                    EmbeddedContinuationWorkspaceRecord.continuation_key == continuation_key,
                    EmbeddedContinuationWorkspaceRecord.continuation_kind == continuation_kind,
                ).delete()
                db.commit()
                self._mark_backend_success()
            finally:
                db.close()
        except Exception as exc:
            self._mark_backend_fallback(f"delete_{continuation_kind}_continuation", exc)
            if not self._allow_operation_fallback:
                raise RuntimeError(self._build_backend_error(f"delete_{continuation_kind}_continuation", exc)) from exc
            if continuation_kind == "tool":
                self._fallback.delete_tool_continuation_descriptor(continuation_key)
            else:
                self._fallback.delete_loop_continuation_descriptor(continuation_key)

    def _mark_backend_success(self) -> None:
        self._fallback_active = False
        self._fallback_reason = ""
        self._last_error = ""

    def _mark_backend_fallback(self, operation: str, exc: Exception) -> None:
        self._fallback_active = True
        self._fallback_reason = str(operation or "").strip()
        self._last_error = str(exc or "").strip()

    def _build_backend_error(self, operation: str, exc: Exception) -> str:
        return (
            f"Embedded workspace store strict_sql failure during {str(operation or '').strip()}: "
            f"{str(exc or '').strip()}"
        )

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
_embedded_workspace_store: Optional[EmbeddedRunWorkspaceStore] = None
ALLOWED_EMBEDDED_WORKSPACE_STORE_MODES = {"memory_only", "prefer_sql_with_fallback", "strict_sql"}


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


def get_embedded_workspace_store() -> EmbeddedRunWorkspaceStore:
    """Return the persistence seam for Embedded SDK run snapshots and continuations."""
    global _embedded_workspace_store
    if _embedded_workspace_store is None:
        if EMBEDDED_WORKSPACE_STORE_MODE == "memory_only":
            _embedded_workspace_store = InMemoryEmbeddedRunWorkspaceStore()
            return _embedded_workspace_store
        try:
            try:
                from database import Base, SessionLocal, engine
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                from backend.database import Base, SessionLocal, engine
            try:
                import models  # noqa: F401
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                import backend.models  # noqa: F401

            Base.metadata.create_all(bind=engine)

            allow_operation_fallback = EMBEDDED_WORKSPACE_STORE_MODE == "prefer_sql_with_fallback"
            _embedded_workspace_store = SQLAlchemyEmbeddedRunWorkspaceStore(
                SessionLocal,
                allow_operation_fallback=allow_operation_fallback,
                backend_mode=EMBEDDED_WORKSPACE_STORE_MODE,
            )
        except Exception as exc:
            if EMBEDDED_WORKSPACE_STORE_MODE == "strict_sql" and DB_MODE != "memory":
                raise RuntimeError(
                    "Embedded workspace store strict_sql mode requires a working SQL backend."
                ) from exc
            _embedded_workspace_store = InMemoryEmbeddedRunWorkspaceStore()
    return _embedded_workspace_store


def get_embedded_workspace_store_mode() -> str:
    return str(EMBEDDED_WORKSPACE_STORE_MODE or "").strip().lower()


def set_embedded_workspace_store_mode(mode: str) -> str:
    normalized_mode = str(mode or "").strip().lower()
    if normalized_mode not in ALLOWED_EMBEDDED_WORKSPACE_STORE_MODES:
        raise ValueError(
            "embedded_workspace_store_mode 仅支持 memory_only / prefer_sql_with_fallback / strict_sql"
        )
    global EMBEDDED_WORKSPACE_STORE_MODE, _embedded_workspace_store
    EMBEDDED_WORKSPACE_STORE_MODE = normalized_mode
    _embedded_workspace_store = None
    return EMBEDDED_WORKSPACE_STORE_MODE
