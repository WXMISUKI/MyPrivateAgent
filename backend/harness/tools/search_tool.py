"""
搜索工具 - 获取信息
"""
import logging
from ..tool_registry import BaseTool, PermissionLevel

try:
    from services.weather_service import weather_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.weather_service import weather_service

logger = logging.getLogger(__name__)


async def search(query: str) -> str:
    """
    搜索信息

    Args:
        query: 搜索查询

    Returns:
        搜索结果
    """
    query_lower = query.lower()

    if weather_service.is_weather_query(query):
        return await weather_service.get_weather_text_for_query(query)

    if "时间" in query or "date" in query_lower or "time" in query_lower:
        from datetime import datetime
        import pytz
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        return f"现在是 {now.strftime('%Y-%m-%d %H:%M:%S')}"

    if "你好" in query or "hello" in query_lower:
        return "你好！有什么可以帮助你的吗？"

    return f"关于'{query}'的信息：未找到相关结果。"


search_tool = BaseTool(
    name="search",
    description="搜索信息，特别是天气、日期时间、一般知识查询。用法: search(query='要搜索的内容')",
    func=search,
    permission_level=PermissionLevel.AUTO,
    parameters={
        "query": {
            "type": "string",
            "description": "搜索查询内容"
        }
    }
)
