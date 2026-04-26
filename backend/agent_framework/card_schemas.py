"""Utilities and constants for structured card schemas."""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple


WEATHER_CARD_SCHEMA = "weather.v1"
DATETIME_CARD_SCHEMA = "datetime.v1"
SEARCH_SUMMARY_CARD_SCHEMA = "search_summary.v1"


def build_datetime_card_from_text(text: str) -> Optional[Dict[str, str]]:
    """Parse datetime tool output into a structured card."""
    if not text:
        return None

    match = re.match(
        r"^(?P<date>\d{4}-\d{2}-\d{2})(?:\s+)(?P<time>\d{2}:\d{2}:\d{2})(?:\s+)(?P<weekday>星期[一二三四五六日])$",
        text.strip(),
    )
    if not match:
        return None

    data = match.groupdict()
    return {
        "kind": "datetime",
        "schema": DATETIME_CARD_SCHEMA,
        "date": data["date"].replace("-", "/"),
        "time": data["time"],
        "weekday": data["weekday"],
    }


def build_search_summary_card(query: str, result: str) -> Optional[Dict[str, str]]:
    """Build a generic structured card for search/retrieval summaries."""
    query = str(query or "").strip()
    result = str(result or "").strip()
    if not query or not result:
        return None

    status = "success"
    if "未找到" in result or "未识别" in result:
        status = "not_found"
    elif "暂时不可用" in result or "查询失败" in result or result.startswith("执行错误:"):
        status = "error"

    summary = result
    prefix = f"关于'{query}'的信息："
    if result.startswith(prefix):
        summary = result[len(prefix):].strip()

    source, source_label, source_count = _infer_search_source(result, status)

    return {
        "kind": "search_summary",
        "schema": SEARCH_SUMMARY_CARD_SCHEMA,
        "query": query,
        "status": status,
        "summary": summary or result,
        "source": source,
        "source_label": source_label,
        "source_count": source_count,
    }


def _infer_search_source(result: str, status: str) -> Tuple[str, str, int]:
    """Infer a stable retrieval source label for generic search summaries."""
    normalized = str(result or "").strip()

    if "知识库" in normalized:
        return "knowledge_base", "知识库", 0 if status != "success" else 1
    if normalized.startswith("你好"):
        return "builtin_runtime", "内置响应", 1
    if "现在是 " in normalized:
        return "system_clock", "系统时间", 1
    if "天气查询结果（" in normalized:
        return "weather_service", "天气服务", 1

    return "search_tool", "搜索工具", 0 if status != "success" else 1
