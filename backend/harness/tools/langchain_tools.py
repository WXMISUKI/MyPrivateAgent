"""
LangChain 工具定义
使用 @tool 装饰器实现真正的工具调用

参考豆包函数调用文档优化：
https://www.volcengine.com/docs/82379/1262342?lang=zh
"""
import json
import logging
from datetime import datetime
from typing import Any, Type, List, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from agent_framework.card_schemas import DATETIME_CARD_SCHEMA, SEARCH_SUMMARY_CARD_SCHEMA, WEATHER_CARD_SCHEMA
    from agent_framework.tools import ToolRenderMode, ToolSpec
    from services.weather_service import weather_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.card_schemas import DATETIME_CARD_SCHEMA, SEARCH_SUMMARY_CARD_SCHEMA, WEATHER_CARD_SCHEMA
    from backend.agent_framework.tools import ToolRenderMode, ToolSpec
    from backend.services.weather_service import weather_service

logger = logging.getLogger(__name__)


class SearchInput(BaseModel):
    """搜索工具输入参数"""
    query: str = Field(
        description="搜索查询内容，用于获取相关信息。例如：'北京天气'、'今天日期'、'某公司信息'等。请一次性提供最完整的查询，不要为同一问题拆成多个近义改写。"
    )


@tool(args_schema=SearchInput)
async def search(query: str) -> str:
    """
    搜索信息工具。

    当用户询问天气、日期时间、一般知识、公司信息、历史事件等问题时使用此工具。
    对同一个问题只调用一次，优先使用最完整、最贴近用户原意的 query。
    天气问题直接使用此工具，不要为了“今天/现在”等时间表达再额外调用 get_current_datetime。

    Args:
        query: 搜索查询内容，应该是完整的问题或关键词

    Returns:
        搜索结果信息，如果未找到相关内容会返回说明
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

    return f"关于'{query}'的信息：我在知识库中未找到相关内容。"


search_input_schema = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "搜索查询内容，用于获取相关信息。例如：'北京天气'、'今天日期'、'某公司信息'等。请一次性给出最完整的查询。"
        }
    },
    "required": ["query"],
    "additionalProperties": False
}


class DateTimeInput(BaseModel):
    """日期时间工具输入参数（空参数）"""
    pass


@tool(args_schema=DateTimeInput)
def get_current_datetime() -> str:
    """
    获取当前日期和时间。

    当用户明确询问当前日期、时间、今天几号、现在是几点、星期几等问题时使用此工具。
    不要为了天气查询、新闻查询等本可直接搜索的问题额外调用此工具。
    此工具不需要任何参数，直接调用即可获取当前系统时间。

    Returns:
        当前日期时间字符串，格式为 YYYY-MM-DD HH:MM:SS 星期X
    """
    import pytz
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)

    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日"
    }

    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} {weekday_map[now.weekday()]}"


datetime_input_schema = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False
}


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "搜索信息工具。当用户询问天气、日期时间、一般知识、公司信息、历史事件等问题时使用此工具。对同一问题只调用一次，并使用最完整的查询语句。天气问题直接调用此工具，不要额外调用 get_current_datetime。",
            "strict": True,
            "parameters": search_input_schema
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "获取当前日期和时间。仅当用户明确询问当前日期、时间、今天几号、现在是几点、星期几等问题时使用；不要为天气查询等问题额外调用。",
            "strict": True,
            "parameters": datetime_input_schema
        }
    }
]

TOOL_SPECS = [
    ToolSpec(
        name="search",
        description="搜索信息、天气、常识等的通用查询工具。",
        permission_level="auto",
        deterministic=False,
        safe_to_rephrase=False,
        render_mode=ToolRenderMode.PLAIN_TEXT,
        supports_cache=True,
        cache_ttl_seconds=300,
        timeout_seconds=10,
        passthrough_strategy="weather_query",
        supported_card_schemas=(WEATHER_CARD_SCHEMA, DATETIME_CARD_SCHEMA, SEARCH_SUMMARY_CARD_SCHEMA),
        tags=("search", "weather", "knowledge"),
    ),
    ToolSpec(
        name="get_current_datetime",
        description="返回当前系统日期和时间。",
        permission_level="auto",
        deterministic=True,
        safe_to_rephrase=False,
        render_mode=ToolRenderMode.STRUCTURED_CARD,
        supports_cache=False,
        timeout_seconds=2,
        passthrough_strategy="always",
        card_schema=DATETIME_CARD_SCHEMA,
        tags=("datetime",),
    ),
]


TOOL_LIST = [search, get_current_datetime]


TOOL_PERMISSIONS = {
    "search": "auto",
    "get_current_datetime": "auto",
}


def get_tools():
    """获取所有工具列表"""
    return TOOL_LIST


def get_tool_by_name(name: str):
    """根据名称获取工具"""
    for t in TOOL_LIST:
        if t.name == name:
            return t
    return None


def get_tool_permission(tool_name: str) -> str:
    """获取工具的权限级别"""
    return TOOL_PERMISSIONS.get(tool_name, "auto")
