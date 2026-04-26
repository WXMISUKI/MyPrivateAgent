"""
权限服务 - 管理 Tool 调用权限
参考 Claude Code 的安全权限控制
"""
import asyncio
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PermissionStatus(Enum):
    """权限状态"""
    PENDING = "pending"      # 等待用户确认
    APPROVED = "approved"    # 用户批准
    DENIED = "denied"       # 用户拒绝
    TIMEOUT = "timeout"     # 超时


@dataclass
class PermissionRequest:
    """权限请求"""
    id: str
    tool_name: str
    tool_args: Dict
    permission_level: str  # 'auto', 'ask', 'deny'
    status: PermissionStatus = PermissionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    result: Optional[str] = None  # 执行结果


class PermissionService:
    """
    权限服务

    管理 Tool 调用的权限请求和确认
    """

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self._pending_requests: Dict[str, PermissionRequest] = {}
        self._completed_results: Dict[str, str] = {}

    def _get_session_factory(self):
        try:
            from database import SessionLocal
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.database import SessionLocal
        return SessionLocal

    def _to_request(self, record) -> PermissionRequest:
        status_value = getattr(record, "status", PermissionStatus.PENDING.value)
        try:
            status = PermissionStatus(status_value)
        except ValueError:
            status = PermissionStatus.PENDING

        return PermissionRequest(
            id=record.request_id,
            tool_name=record.tool_name,
            tool_args=dict(record.tool_args or {}),
            permission_level=record.permission_level,
            status=status,
            created_at=record.created_at or datetime.now(),
            user_id=record.user_id,
            conversation_id=record.conversation_id,
            result=record.result,
        )

    def _save_request(self, request: PermissionRequest) -> None:
        try:
            try:
                from models import PermissionRequestRecord
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                from backend.models import PermissionRequestRecord

            session_factory = self._get_session_factory()
            db = session_factory()
            try:
                record = db.query(PermissionRequestRecord).filter(
                    PermissionRequestRecord.request_id == request.id
                ).first()
                if record is None:
                    record = PermissionRequestRecord(request_id=request.id)
                    db.add(record)

                record.tool_name = request.tool_name
                record.tool_args = request.tool_args
                record.permission_level = request.permission_level
                record.status = request.status.value
                record.user_id = request.user_id
                record.conversation_id = request.conversation_id
                record.result = request.result
                if request.status in (PermissionStatus.APPROVED, PermissionStatus.DENIED, PermissionStatus.TIMEOUT):
                    record.completed_at = datetime.now()

                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"[PermissionService] 持久化权限请求失败，回退内存态: {e}")

    def _load_record(self, request_id: str) -> Optional[PermissionRequest]:
        try:
            try:
                from models import PermissionRequestRecord
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                from backend.models import PermissionRequestRecord

            session_factory = self._get_session_factory()
            db = session_factory()
            try:
                record = db.query(PermissionRequestRecord).filter(
                    PermissionRequestRecord.request_id == request_id
                ).first()
                return self._to_request(record) if record else None
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"[PermissionService] 读取权限请求失败: {e}")
            return None

    def create_request(
        self,
        tool_name: str,
        tool_args: Dict,
        permission_level: str,
        user_id: int = None,
        conversation_id: int = None
    ) -> PermissionRequest:
        """
        创建权限请求

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            permission_level: 权限级别
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            权限请求对象
        """
        import uuid
        request_id = str(uuid.uuid4())[:8]

        request = PermissionRequest(
            id=request_id,
            tool_name=tool_name,
            tool_args=tool_args,
            permission_level=permission_level,
            user_id=user_id,
            conversation_id=conversation_id
        )

        self._pending_requests[request_id] = request
        self._save_request(request)
        logger.info(f"[PermissionService] 创建权限请求: {request_id} - {tool_name}")

        return request

    def get_request(self, request_id: str) -> Optional[PermissionRequest]:
        """获取权限请求"""
        request = self._pending_requests.get(request_id)
        if request:
            return request
        return self._load_record(request_id)

    def approve(self, request_id: str, result: str = None) -> bool:
        """
        批准权限请求

        Args:
            request_id: 请求ID
            result: 可选的执行结果

        Returns:
            是否成功
        """
        request = self._pending_requests.get(request_id)
        if request is None:
            request = self._load_record(request_id)
            if request is not None:
                self._pending_requests[request_id] = request
        if not request:
            logger.warning(f"[PermissionService] 请求不存在: {request_id}")
            return False

        request.status = PermissionStatus.APPROVED
        request.result = result
        self._completed_results[request_id] = result or "approved"
        self._save_request(request)
        logger.info(f"[PermissionService] 批准权限请求: {request_id}")

        return True

    def deny(self, request_id: str) -> bool:
        """
        拒绝权限请求

        Args:
            request_id: 请求ID

        Returns:
            是否成功
        """
        request = self._pending_requests.get(request_id)
        if request is None:
            request = self._load_record(request_id)
            if request is not None:
                self._pending_requests[request_id] = request
        if not request:
            logger.warning(f"[PermissionService] 请求不存在: {request_id}")
            return False

        request.status = PermissionStatus.DENIED
        self._completed_results[request_id] = "denied"
        self._save_request(request)
        logger.info(f"[PermissionService] 拒绝权限请求: {request_id}")

        return True

    def get_result(self, request_id: str) -> Optional[str]:
        """获取请求结果（用于恢复挂起的执行）"""
        result = self._completed_results.get(request_id)
        if result is not None:
            return result

        request = self._load_record(request_id)
        return request.result if request else None

    def is_pending(self, request_id: str) -> bool:
        """检查请求是否还在等待"""
        request = self._pending_requests.get(request_id)
        return request is not None and request.status == PermissionStatus.PENDING

    def cleanup_old_requests(self, max_age_seconds: int = 300):
        """清理过期的请求"""
        import time
        now = datetime.now()
        expired = []

        for req_id, request in self._pending_requests.items():
            age = (now - request.created_at).total_seconds()
            if age > max_age_seconds:
                expired.append(req_id)

        for req_id in expired:
            request = self._pending_requests.pop(req_id, None)
            if request and request.status == PermissionStatus.PENDING:
                request.status = PermissionStatus.TIMEOUT
                self._completed_results[req_id] = "timeout"
                self._save_request(request)
                logger.info(f"[PermissionService] 清理过期请求: {req_id}")

    def list_pending_requests(self, user_id: int = None) -> List[PermissionRequest]:
        """列出待处理的请求"""
        requests = list(self._pending_requests.values())

        try:
            try:
                from models import PermissionRequestRecord
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                from backend.models import PermissionRequestRecord

            session_factory = self._get_session_factory()
            db = session_factory()
            try:
                query = db.query(PermissionRequestRecord).filter(
                    PermissionRequestRecord.status == PermissionStatus.PENDING.value
                )
                if user_id is not None:
                    query = query.filter(PermissionRequestRecord.user_id == user_id)
                records = query.order_by(PermissionRequestRecord.created_at.asc()).all()
                persisted = [self._to_request(record) for record in records]
                request_map = {request.id: request for request in persisted}
                for request in requests:
                    request_map[request.id] = request
                return list(request_map.values())
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"[PermissionService] 列出待处理权限请求失败，回退内存态: {e}")

        if user_id is not None:
            requests = [r for r in requests if r.user_id == user_id]

        return [r for r in requests if r.status == PermissionStatus.PENDING]


# 全局权限服务实例
permission_service = PermissionService()


def get_permission_service() -> PermissionService:
    """获取全局权限服务"""
    return permission_service
