"""Completion evaluator for composite requests in the general agent demo."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


TRAVEL_COMPLETENESS_HINTS = {
    "weather": ("天气", "气温", "降雨", "风速", "适合", "不适合"),
    "transport": ("交通", "高铁", "动车", "大巴", "轮渡", "自驾", "路线", "怎么去"),
    "play": ("景点", "游玩", "攻略", "推荐", "打卡", "安排", "行程"),
}

RESEARCH_COMPLETENESS_HINTS = {
    "options": ("方案", "选项", "候选", "方式", "路线", "模型", "工具"),
    "evidence": ("来源", "依据", "信息", "数据", "结果", "结论"),
    "recommendation": ("建议", "推荐", "适合", "优先", "结论", "可以考虑"),
}

PLANNING_COMPLETENESS_HINTS = {
    "goal": ("目标", "问题", "任务", "要做什么", "范围"),
    "steps": ("步骤", "计划", "拆解", "阶段", "todo", "待办"),
    "risks": ("风险", "注意", "依赖", "阻塞", "前提"),
}


REQUEST_PROFILES = {
    "travel_planning": {
        "missing_labels": {
            "weather": "天气信息",
            "transport": "交通建议",
            "play": "游玩/行程建议",
        },
        "capability_suggestions": {
            "weather": [
                "补充更稳定的天气/地理位置工具，避免天气信息只覆盖单一维度。",
            ],
            "transport": [
                "增加交通路线检索工具，或接入地图 / 出行类 MCP capability。",
                "增加出发地到目的地的结构化路线规划能力。",
            ],
            "play": [
                "增加 POI / 景点检索工具，或接入旅游攻略类 MCP capability。",
                "增加面向行程编排的目的地知识源或攻略检索能力。",
            ],
        },
    },
    "research_compare": {
        "missing_labels": {
            "options": "候选方案",
            "evidence": "可靠依据",
            "recommendation": "最终建议",
        },
        "capability_suggestions": {
            "options": [
                "增加更稳定的检索或目录类工具，确保能覆盖多个候选方案。",
            ],
            "evidence": [
                "增加可引用来源的搜索工具、知识库或 MCP capability。",
            ],
            "recommendation": [
                "增加结构化对比模板或决策支持型 Skill，帮助形成可交付结论。",
            ],
        },
    },
    "planning": {
        "missing_labels": {
            "goal": "任务目标",
            "steps": "可执行步骤",
            "risks": "风险或依赖说明",
        },
        "capability_suggestions": {
            "goal": [
                "增加更清晰的任务定义模板或输入约束，避免目标描述过于模糊。",
            ],
            "steps": [
                "增加结构化计划生成模板或 Planner Skill，提升步骤拆解稳定性。",
            ],
            "risks": [
                "增加依赖检查、前提校验或风险识别型 Skill / MCP capability。",
            ],
        },
    },
}


class CompletionEvaluatorService:
    """Evaluate whether a composite task should continue, retry once, or finalize."""

    def detect_request_profile(self, user_goal: str) -> Optional[str]:
        if self.is_travel_planning_goal(user_goal):
            return "travel_planning"
        if self.is_research_compare_goal(user_goal):
            return "research_compare"
        if self.is_task_planning_goal(user_goal):
            return "planning"
        return None

    def is_composite_goal(self, user_goal: str) -> bool:
        return self.detect_request_profile(user_goal) is not None

    def is_travel_planning_goal(self, user_goal: str) -> bool:
        if not user_goal:
            return False
        lowered = user_goal.lower()
        travel_keywords = ("旅游", "旅行", "攻略", "行程", "出发", "怎么去", "交通", "景点", "玩", "trip", "travel", "itinerary", "route")
        weather_keywords = ("天气", "气温", "温度", "weather", "forecast")
        return any(keyword in user_goal or keyword in lowered for keyword in travel_keywords) and any(
            keyword in user_goal or keyword in lowered for keyword in weather_keywords
        )

    def is_research_compare_goal(self, user_goal: str) -> bool:
        if not user_goal:
            return False
        lowered = user_goal.lower()
        compare_keywords = ("对比", "比较", "优缺点", "区别", "选哪个", "哪个好", "方案", "推荐", "research", "compare", "comparison")
        evidence_keywords = ("为什么", "依据", "原因", "分析", "调研", "资料", "source", "evidence")
        return any(keyword in user_goal or keyword in lowered for keyword in compare_keywords) and any(
            keyword in user_goal or keyword in lowered for keyword in evidence_keywords
        )

    def is_task_planning_goal(self, user_goal: str) -> bool:
        if not user_goal:
            return False
        lowered = user_goal.lower()
        planning_keywords = ("计划", "规划", "拆解", "步骤", "todo", "待办", "分阶段", "roadmap", "plan")
        action_keywords = ("如何做", "怎么做", "落地", "执行", "推进", "实施", "安排", "完成")
        return any(keyword in user_goal or keyword in lowered for keyword in planning_keywords) and any(
            keyword in user_goal or keyword in lowered for keyword in action_keywords
        )

    def summarize_tool_observation(self, result: str) -> str:
        lines = [line.strip() for line in str(result or "").splitlines() if line.strip()]
        if not lines:
            return ""
        summary = "；".join(lines[:3])
        return summary[:180]

    def build_synthesis_instruction(self, user_goal: str) -> str:
        profile = self.detect_request_profile(user_goal)
        if profile == "travel_planning":
            return (
                "你正在处理复合型旅行规划请求。已有工具结果只作为中间观察，不能直接停止。"
                "请基于已有观察结果继续生成最终答复。最终答复至少覆盖："
                "1. 目的地天气判断；2. 交通/到达建议；3. 游玩或行程建议；4. 注意事项。"
                "如果已有工具结果仍不足以支撑完整结论，请明确说明当前缺口，并基于已知信息给出保守建议。"
            )
        if profile == "research_compare":
            return (
                "你正在处理复合型研究/对比请求。已有工具结果只作为中间观察，不能直接停止。"
                "请基于已有观察继续生成最终答复。最终答复至少覆盖："
                "1. 候选方案或关键选项；2. 支撑依据或观察结果；3. 综合建议。"
                "如果已有工具结果仍不足以支撑完整结论，请明确说明当前缺口，并给出保守建议。"
            )
        if profile == "planning":
            return (
                "你正在处理复合型规划请求。已有工具结果只作为中间观察，不能直接停止。"
                "请基于已有观察继续生成最终答复。最终答复至少覆盖："
                "1. 目标与范围；2. 分步骤执行计划；3. 风险、依赖或注意事项。"
                "如果已有工具结果仍不足以支撑完整结论，请明确说明当前缺口，并给出保守建议。"
            )
        return ""

    def get_missing_part_labels(self, profile: Optional[str], missing_parts: List[str]) -> List[str]:
        labels = REQUEST_PROFILES.get(profile or "", {}).get("missing_labels", {})
        return [str(labels.get(part, part)) for part in missing_parts]

    def build_capability_gap_suggestions(self, profile: Optional[str], missing_parts: List[str]) -> List[str]:
        suggestion_map = REQUEST_PROFILES.get(profile or "", {}).get("capability_suggestions", {})
        suggestions: List[str] = []
        for key in missing_parts:
            suggestions.extend(suggestion_map.get(key, []))
        deduped: List[str] = []
        seen = set()
        for item in suggestions:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped

    def evaluate(
        self,
        *,
        user_goal: str,
        tool_results: List[Dict[str, Any]],
        tool_call_history: List[Dict[str, Any]],
        max_similar_tool_calls: int,
    ) -> Optional[Dict[str, Any]]:
        profile = self.detect_request_profile(user_goal)
        if not profile:
            return None
        if not tool_call_history:
            return None

        aggregated = "\n".join(str(item.get("result", "") or "") for item in tool_call_history)
        if not aggregated.strip():
            return None

        if profile == "travel_planning":
            hints = TRAVEL_COMPLETENESS_HINTS
        elif profile == "research_compare":
            hints = RESEARCH_COMPLETENESS_HINTS
        else:
            hints = PLANNING_COMPLETENESS_HINTS
        missing_parts = [
            part
            for part, keywords in hints.items()
            if not any(keyword in aggregated for keyword in keywords)
        ]
        if not missing_parts:
            return None

        search_history = [item for item in tool_call_history if item.get("name") == "search"]
        search_attempts = len(search_history)
        latest_search = search_history[-1] if search_history else None
        latest_result = str((latest_search or {}).get("result", "") or "")
        latest_args = dict((latest_search or {}).get("args", {}) or {})
        latest_query = str(latest_args.get("query", "") or "")

        weather_only_observation = latest_result.startswith("天气查询结果（")
        needs_retry = (
            (profile == "travel_planning" and weather_only_observation)
            or (profile in {"research_compare", "planning"} and search_attempts < max_similar_tool_calls)
        )
        if needs_retry and search_attempts < max_similar_tool_calls:
            retry_query = self._build_retry_query(user_goal=user_goal, latest_query=latest_query, missing_parts=missing_parts)
            if retry_query and retry_query != latest_query:
                return {
                    "action": "retry",
                    "reason": "当前结果仍不完整，准备按缺失维度补查一次。",
                    "missing_parts": missing_parts,
                    "profile": profile,
                    "retry_tool_call": {
                        "name": "search",
                        "arguments": {"query": retry_query},
                    },
                    "status_message": self._build_retry_status_message(profile, missing_parts),
                }

        if search_attempts < max_similar_tool_calls:
            return None

        missing_text = "、".join(self.get_missing_part_labels(profile, missing_parts))
        return {
            "action": "finalize",
            "should_finalize": True,
            "stop_reason": "tool_result_incomplete",
            "missing_parts": missing_parts,
            "profile": profile,
            "message": (
                f"我已经尝试检索了与这次请求相关的信息，但当前工具结果仍缺少{missing_text}。"
                "这说明仅靠现有检索结果还不足以给出高质量的完整方案。"
                "如果你愿意，我可以下一步基于已有结果先给你一个保守的人工整理版建议；"
                "或者你也可以把问题拆成更具体的子问题分别来问。"
            ),
        }

    def _build_retry_query(self, *, user_goal: str, latest_query: str, missing_parts: List[str]) -> str:
        if not missing_parts:
            return ""

        parts: List[str] = []
        if "transport" in missing_parts:
            parts.append("福州到舟山的交通方式和到达建议")
        if "play" in missing_parts:
            parts.append("舟山热门景点、游玩路线和旅行注意事项")
        if "weather" in missing_parts:
            parts.append("舟山明天天气")
        if "options" in missing_parts:
            parts.append("候选方案 对比 依据 推荐")
        if "evidence" in missing_parts:
            parts.append("方案 分析 依据 资料 来源")
        if "recommendation" in missing_parts:
            parts.append("最终建议 适合场景 结论")
        if "goal" in missing_parts:
            parts.append("任务目标 范围 输出要求")
        if "steps" in missing_parts:
            parts.append("执行步骤 计划拆解 todo")
        if "risks" in missing_parts:
            parts.append("风险 依赖 阻塞 注意事项")

        retry_query = "；".join(parts).strip("； ")
        if not retry_query:
            retry_query = user_goal.strip()
        if retry_query == latest_query.strip():
            return ""
        return retry_query

    def _build_retry_status_message(self, profile: Optional[str], missing_parts: List[str]) -> str:
        if profile == "travel_planning":
            return "已拿到天气结果，正在补查交通与游玩建议。"
        if profile == "research_compare":
            labels = "、".join(self.get_missing_part_labels(profile, missing_parts))
            return f"当前结果仍缺少{labels}，正在补查一次。"
        if profile == "planning":
            labels = "、".join(self.get_missing_part_labels(profile, missing_parts))
            return f"当前规划结果仍缺少{labels}，正在补查一次。"
        return "当前结果仍不完整，正在补查一次。"


_completion_evaluator_service: Optional[CompletionEvaluatorService] = None


def get_completion_evaluator_service() -> CompletionEvaluatorService:
    global _completion_evaluator_service
    if _completion_evaluator_service is None:
        _completion_evaluator_service = CompletionEvaluatorService()
    return _completion_evaluator_service
