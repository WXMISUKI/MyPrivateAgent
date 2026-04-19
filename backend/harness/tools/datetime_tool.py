"""
日期时间工具 - 获取当前日期和时间
"""
import logging
from datetime import datetime
import pytz
from ..tool_registry import BaseTool, PermissionLevel

logger = logging.getLogger(__name__)


async def get_current_datetime() -> str:
    """
    获取当前日期时间

    Returns:
        当前日期时间字符串
    """
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


datetime_tool = BaseTool(
    name="get_current_datetime",
    description="获取当前的日期和时间。无需参数。",
    func=get_current_datetime,
    permission_level=PermissionLevel.AUTO,
    parameters={}
)
