"""Startup diagnostics and lightweight health inspection for stable demos."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import text

try:
    from agent_server.config import PROJECT_ROOT, get_available_server_presets
    from config import ARK_API_KEY, DATABASE_URL, DB_MODE, DEFAULT_MODEL, SQLITE_PATH
    from database import engine
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.config import PROJECT_ROOT, get_available_server_presets
    from backend.config import ARK_API_KEY, DATABASE_URL, DB_MODE, DEFAULT_MODEL, SQLITE_PATH
    from backend.database import engine


class StartupDiagnosticsService:
    """Collect environment, filesystem, and API-readiness diagnostics."""

    def collect_report(self) -> Dict[str, Any]:
        checks = {
            "environment": self._check_environment(),
            "database": self._check_database(),
            "filesystem": self._check_filesystem(),
            "ui": self._check_ui_assets(),
            "models": self._check_models(),
            "presets": self._check_presets(),
        }
        statuses = [entry["status"] for entry in checks.values()]
        overall_status = "ok"
        if any(status == "fail" for status in statuses):
            overall_status = "fail"
        elif any(status == "warn" for status in statuses):
            overall_status = "warn"

        return {
            "status": overall_status,
            "checks": checks,
            "summary": self._build_summary(checks),
        }

    def _check_environment(self) -> Dict[str, Any]:
        env_path = PROJECT_ROOT / ".env"
        details: List[str] = []
        status = "ok"

        if not env_path.exists():
            status = "fail"
            details.append("缺少项目根目录 .env 文件")
        else:
            details.append(f".env 已存在: {env_path}")

        if not DEFAULT_MODEL:
            status = "fail"
            details.append("DEFAULT_MODEL 未配置")
        else:
            details.append(f"默认模型: {DEFAULT_MODEL}")

        details.append(f"存储模式: {DB_MODE}")
        if DB_MODE == "sqlite":
            details.append(f"本地 SQLite 路径: {SQLITE_PATH}")
        else:
            details.append("当前启用外部 MySQL 模式")

        if DEFAULT_MODEL == "doubao" and not ARK_API_KEY:
            status = "warn" if status != "fail" else status
            details.append("当前默认模型为 doubao，但 ARK_API_KEY 未配置")

        return {"status": status, "details": details}

    def _check_database(self) -> Dict[str, Any]:
        details: List[str] = []
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1")).scalar()
            details.append(f"数据库连接正常: SELECT {result}")
            details.append(f"连接地址: {DATABASE_URL}")
            return {"status": "ok", "details": details}
        except Exception as exc:  # pragma: no cover - runtime dependent
            details.append(f"数据库连接失败: {exc}")
            return {"status": "fail", "details": details}

    def _check_filesystem(self) -> Dict[str, Any]:
        details: List[str] = []
        status = "ok"

        required_paths = {
            "backend/data": PROJECT_ROOT / "backend" / "data",
            "skill_store": PROJECT_ROOT / "skill_store",
            "问题记录": PROJECT_ROOT / "问题记录",
            "docs": PROJECT_ROOT / "docs",
        }
        for label, path in required_paths.items():
            if path.exists():
                details.append(f"{label} 已存在")
            else:
                path.mkdir(parents=True, exist_ok=True)
                status = "warn" if status == "ok" else status
                details.append(f"{label} 缺失，已自动创建: {path}")

        return {"status": status, "details": details}

    def _check_ui_assets(self) -> Dict[str, Any]:
        details: List[str] = []
        dist_dir = PROJECT_ROOT / "frontend-vue" / "dist"
        assets_dir = dist_dir / "assets"
        if dist_dir.exists() and assets_dir.exists():
            details.append("Vue SPA 构建产物已就绪")
            return {"status": "ok", "details": details}

        details.append("Vue SPA 构建产物缺失，生产模式将回退或无法展示，请先执行 npm run build")
        return {"status": "warn", "details": details}

    def _check_models(self) -> Dict[str, Any]:
        details: List[str] = []
        status = "ok"
        available = {"doubao", "deepseek-r1:7b", "qwen2.5:7b", "llama3.1"}

        if DEFAULT_MODEL not in available:
            status = "warn"
            details.append(f"默认模型 `{DEFAULT_MODEL}` 不在内置已知列表中，请确认配置")
        else:
            details.append(f"默认模型 `{DEFAULT_MODEL}` 在已知列表中")

        return {"status": status, "details": details}

    def _check_presets(self) -> Dict[str, Any]:
        presets = list(get_available_server_presets())
        return {
            "status": "ok",
            "details": [f"可用 preset: {', '.join(presets)}"],
        }

    @staticmethod
    def _build_summary(checks: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        summary = {"ok": 0, "warn": 0, "fail": 0}
        for item in checks.values():
            status = item.get("status", "warn")
            summary[status] = summary.get(status, 0) + 1
        return summary


_startup_diagnostics_service: StartupDiagnosticsService | None = None


def get_startup_diagnostics_service() -> StartupDiagnosticsService:
    global _startup_diagnostics_service
    if _startup_diagnostics_service is None:
        _startup_diagnostics_service = StartupDiagnosticsService()
    return _startup_diagnostics_service
