"""
Graph State - 状态定义与 Reducer

对标 LangGraph 的 TypedDict + Annotated reducer 模式。
状态字段通过 Annotated 注解指定合并策略，支持消息追加、计数累加等。
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Callable, TypedDict


# ---------------------------------------------------------------------------
# Reducer functions
# ---------------------------------------------------------------------------

def add_messages(existing: list, new: list) -> list:
    """合并消息列表：追加新消息到现有列表。"""
    if not new:
        return existing or []
    if not existing:
        return list(new)
    return list(existing) + list(new)


def merge_dicts(existing: dict, new: dict) -> dict:
    """合并字典：新值覆盖旧值。"""
    if not existing:
        return dict(new) if new else {}
    merged = dict(existing)
    if new:
        merged.update(new)
    return merged


def add_values(existing: Any, new: Any) -> Any:
    """累加数值。"""
    if existing is None:
        return new
    if new is None:
        return existing
    return existing + new


# ---------------------------------------------------------------------------
# Standard message state (used by most agents)
# ---------------------------------------------------------------------------

class MessagesState(TypedDict, total=False):
    """标准消息状态，messages 字段使用 add_messages reducer。"""
    messages: Annotated[list[dict], add_messages]
    context: Annotated[dict, merge_dicts]
    metadata: Annotated[dict, merge_dicts]


# Known reducers for standard state schemas
_KNOWN_REDUCERS: dict[str, dict[str, Callable]] = {
    "MessagesState": {
        "messages": add_messages,
        "context": merge_dicts,
        "metadata": merge_dicts,
    },
}


# ---------------------------------------------------------------------------
# State schema introspection
# ---------------------------------------------------------------------------

def get_reducer(field_type: Any) -> Callable | None:
    """从 Annotated 类型中提取 reducer 函数。"""
    if hasattr(field_type, "__metadata__"):
        for meta in field_type.__metadata__:
            if callable(meta):
                return meta
    return None


def get_base_type(field_type: Any) -> type:
    """从 Annotated 类型中提取基础类型。"""
    if hasattr(field_type, "__origin__") and field_type.__origin__ is Annotated:
        return field_type.__args__[0]
    return field_type


def merge_state(schema: type, current: dict, update: dict) -> dict:
    """根据 state schema 的 reducer 定义合并状态。

    优先使用 schema 注解中的 Annotated reducer，
    如果找不到，回退到已知的 reducer 映射，
    最后按默认覆盖方式处理。
    """
    result = dict(current)
    schema_name = getattr(schema, "__name__", "")
    known = _KNOWN_REDUCERS.get(schema_name, {})

    for key, value in update.items():
        if value is None:
            continue

        if key not in result:
            result[key] = value
            continue

        # 1. 尝试从 Annotated 注解获取 reducer
        field_type = schema.__annotations__.get(key)
        reducer = None
        if field_type:
            reducer = get_reducer(field_type)

        # 2. 回退到已知 reducer
        if reducer is None:
            reducer = known.get(key)

        # 3. 应用 reducer 或默认覆盖
        if reducer:
            result[key] = reducer(result[key], value)
        else:
            result[key] = value

    return result
