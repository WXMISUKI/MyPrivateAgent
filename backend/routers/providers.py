"""Provider configuration management API."""

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from services.provider_config_service import get_provider_config_service
    from services.provider_failover_analytics_service import get_provider_failover_analytics_service
    from database import get_db
except ModuleNotFoundError:
    from backend.services.provider_config_service import get_provider_config_service
    from backend.services.provider_failover_analytics_service import get_provider_failover_analytics_service
    from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["providers"])


class ProviderUpdateRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


@router.get("/providers")
def list_providers():
    """List all known providers with their configuration status."""
    return get_provider_config_service().list_providers()


@router.patch("/providers/{provider_name}")
def update_provider(provider_name: str, request: ProviderUpdateRequest):
    """Update a provider's API key and/or base URL."""
    try:
        result = get_provider_config_service().update_provider(
            provider_name,
            request.model_dump(exclude_none=True),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/providers/{provider_name}/test")
def test_provider(provider_name: str):
    """Test connectivity to a provider."""
    service = get_provider_config_service()
    effective = service.get_effective_config(provider_name)

    if effective.get("config_source") == "unconfigured":
        return {"status": "error", "message": "Provider 未配置"}

    base_url = effective.get("base_url", "").rstrip("/")
    api_key = effective.get("api_key", "")

    if provider_name == "ollama":
        return _test_ollama(base_url)
    elif provider_name == "volcengine-ark":
        return _test_volcengine_ark(base_url, api_key)
    else:
        return {"status": "error", "message": f"不支持测试的 provider: {provider_name}"}


def _test_ollama(base_url: str) -> dict:
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        model_count = len(data.get("models", []))
        return {
            "status": "ok",
            "message": f"连接成功，发现 {model_count} 个模型",
            "model_count": model_count,
            "latency_ms": round(response.elapsed.total_seconds() * 1000),
        }
    except httpx.ConnectError:
        return {"status": "error", "message": f"无法连接到 {base_url}，请确认 Ollama 服务已启动"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _test_volcengine_ark(base_url: str, api_key: str) -> dict:
    if not api_key:
        return {"status": "error", "message": "API Key 未配置"}
    try:
        response = httpx.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if response.status_code == 401:
            return {"status": "error", "message": "API Key 无效（401 Unauthorized）"}
        if response.status_code == 200:
            return {
                "status": "ok",
                "message": "API Key 验证成功",
                "latency_ms": round(response.elapsed.total_seconds() * 1000),
            }
        return {
            "status": "warning",
            "message": f"连接成功但返回状态码 {response.status_code}",
            "latency_ms": round(response.elapsed.total_seconds() * 1000),
        }
    except httpx.ConnectError:
        return {"status": "error", "message": f"无法连接到 {base_url}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/failover-analytics")
def get_failover_analytics(
    window_days: int = 7,
    limit: int = 500,
    db=Depends(get_db),
):
    """Return provider failover analytics summary for runtime operations."""
    if window_days not in {7, 14, 30}:
        raise HTTPException(status_code=400, detail="window_days 仅支持 7/14/30")
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit 范围应在 1-5000")
    return get_provider_failover_analytics_service(db).get_summary(window_days=window_days, limit=limit)
