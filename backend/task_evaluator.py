"""
任务复杂度评估器
自动评估任务复杂度，决定使用单智能体还是多智能体模式
"""
import json
import re
from typing import Literal, Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

try:
    from model_router import get_model_router
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.model_router import get_model_router


class QuickAssessment(BaseModel):
    """快速评估结果"""
    is_simple: bool
    confidence: float
    reasoning: str = ""


class DetailedAssessment(BaseModel):
    """详细评估结果"""
    task_type: Literal["simple_dialog", "info_query", "complex_research", "multi_comparison", "development_task"]
    needs_multi_agent: bool
    recommended_agents: int
    reasoning: str
    subtasks: list = []


class CostBenefitResult(BaseModel):
    """成本效益分析结果"""
    single_cost: float
    multi_cost: float
    expected_benefit: float
    beneficial: bool
    reasoning: str = ""


class TaskComplexityResult(BaseModel):
    """任务复杂度评估最终结果"""
    mode: Literal["single", "multi"]
    num_subagents: int = 0
    reasoning: str
    confidence: float
    cost_benefit: Optional[CostBenefitResult] = None


class TaskComplexityEvaluator:
    """任务复杂度评估器"""

    # 任务类型映射
    TASK_TYPES = {
        "simple_dialog": "简单对话",
        "info_query": "信息查询",
        "complex_research": "复杂研究",
        "multi_comparison": "多维比较",
        "development_task": "开发任务"
    }

    # 简单对话指示器
    SIMPLE_INDICATORS = [
        (r"^(你好|hi|hello|hey|嗨)$", "问候"),
        (r"^(谢谢|thank|感谢|多谢)", "感谢"),
        (r"^(再见|bye|goodbye|拜拜)", "告别"),
        (r"^(是|否|yes|no|对|错)$", "简单回答"),
    ]

    # 复杂任务关键词
    COMPLEX_KEYWORDS = [
        "研究", "分析", "比较", "开发", "设计", "实现",
        "research", "analyze", "compare", "develop", "design", "implement"
    ]

    # 任务类型关键词
    TASK_KEYWORDS = {
        "research": "complex_research",
        "研究": "complex_research",
        "compare": "multi_comparison",
        "比较": "multi_comparison",
        "analyze": "complex_research",
        "分析": "complex_research",
        "develop": "development_task",
        "开发": "development_task",
        "design": "development_task",
        "设计": "development_task",
    }

    def __init__(self):
        self.router = get_model_router()
        # 使用豆包作为主要评估模型，如果不可用则降级使用本地模型
        try:
            self.model = self.router.get_model("doubao")
            self.model_name = "doubao"
        except ValueError:
            # 豆包模型未配置，使用本地模型
            try:
                self.model = self.router.get_model("llama3.1")
                self.model_name = "llama3.1"
                print("警告: 豆包模型未配置，使用 llama3.1 作为评估模型")
            except ValueError:
                # 如果本地模型也不可用，使用 deepseek-r1:7b
                self.model = self.router.get_model("deepseek-r1:7b")
                self.model_name = "deepseek-r1:7b"
                print("警告: 使用 deepseek-r1:7b 作为评估模型")

    async def evaluate(self, user_message: str) -> TaskComplexityResult:
        """
        评估任务复杂度并决定使用模式（简化版）

        Args:
            user_message: 用户消息

        Returns:
            任务复杂度评估结果
        """
        # 只做快速评估，简化流程
        quick_assessment = self._quick_assess(user_message)

        # 简单问题直接返回单智能体模式
        if quick_assessment.is_simple:
            return TaskComplexityResult(
                mode="single",
                num_subagents=0,
                reasoning=f"简单对话（{quick_assessment.reasoning}），使用单智能体模式",
                confidence=quick_assessment.confidence
            )

        # 默认使用单智能体模式（避免多智能体流程）
        return TaskComplexityResult(
            mode="single",
            num_subagents=0,
            reasoning=f"使用单智能体模式（{quick_assessment.reasoning}）",
            confidence=0.7
        )

    def _quick_assess(self, user_message: str) -> QuickAssessment:
        """快速评估（基于规则）"""
        message_lower = user_message.lower().strip()
        message_len = len(user_message)

        # 检查简单指示器（优先级最高）
        for pattern, reason in self.SIMPLE_INDICATORS:
            if re.match(pattern, message_lower):
                return QuickAssessment(
                    is_simple=True,
                    confidence=0.95,
                    reasoning=reason
                )

        # 检查是否包含复杂关键词（优先级高于消息长度）
        has_complex_keywords = any(
            keyword in message_lower
            for keyword in self.COMPLEX_KEYWORDS
        )

        if has_complex_keywords:
            return QuickAssessment(
                is_simple=False,
                confidence=0.8,
                reasoning="包含复杂任务关键词"
            )

        # 检查消息长度
        if message_len < 30:
            return QuickAssessment(
                is_simple=True,
                confidence=0.7,
                reasoning="消息过短"
            )

        # 默认为简单任务
        return QuickAssessment(
            is_simple=True,
            confidence=0.6,
            reasoning="无复杂任务关键词"
        )

    async def _detailed_assess(self, user_message: str) -> DetailedAssessment:
        """详细评估（使用模型）"""
        prompt = f"""分析以下任务的复杂度：

任务: {user_message}

请评估：
1. 任务类型（simple_dialog/info_query/complex_research/multi_comparison/development_task）
2. 是否需要多个智能体并行工作
3. 推荐的子智能体数量（0-5，0 表示不需要）
4. 分析理由

返回 JSON 格式：
{{
    "task_type": "任务类型",
    "needs_multi_agent": true/false,
    "recommended_agents": 数量,
    "reasoning": "分析理由"
}}"""

        try:
            # 使用同步的invoke方法，然后在异步函数中运行
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.invoke, [HumanMessage(content=prompt)])
            content = response.content.strip()

            # 尝试提取 JSON
            json_match = re.search(r'\{[^}]*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                # 如果无法提取 JSON，使用默认值
                data = {
                    "task_type": "info_query",
                    "needs_multi_agent": False,
                    "recommended_agents": 0,
                    "reasoning": "无法解析模型输出，使用默认值"
                }

            return DetailedAssessment(**data)

        except Exception as e:
            # 出错时返回默认值
            return DetailedAssessment(
                task_type="info_query",
                needs_multi_agent=False,
                recommended_agents=0,
                reasoning=f"评估出错: {str(e)}"
            )

    def _cost_benefit_analysis(
        self,
        assessment: DetailedAssessment
    ) -> CostBenefitResult:
        """成本效益分析"""
        # Token 成本估算（单位：美元）
        # 假设成本：$0.001 / 1K tokens

        # 单智能体成本
        # 输入: 1K tokens (用户消息)
        # 输出: 2K tokens (模型回答)
        single_tokens = 3  # K tokens
        single_cost = single_tokens * 0.001

        # 多智能体成本
        # 主智能体: 输入 1K, 输出 1K (任务分解)
        # 子智能体: 每个输入 2K (子任务), 输出 2K (结果)
        # 主智能体: 输入 2K (所有结果), 输出 2K (最终答案)
        num_subagents = assessment.recommended_agents
        multi_tokens = 2 + (4 * num_subagents) + 4  # K tokens
        multi_cost = multi_tokens * 0.001

        # 预期收益（质量提升百分比）
        benefit_map = {
            "simple_dialog": 0.0,
            "info_query": 0.05,
            "complex_research": 0.5,
            "multi_comparison": 0.4,
            "development_task": 0.6
        }

        expected_benefit = benefit_map.get(assessment.task_type, 0.1)

        # 成本增加是否值得
        cost_increase = multi_cost - single_cost
        # 收益需要是成本增加的 15 倍才值得
        beneficial = expected_benefit > cost_increase * 15

        reasoning = f"""
单智能体成本: ${single_cost:.4f}
多智能体成本: ${multi_cost:.4f}
成本增加: ${cost_increase:.4f}
预期收益: {expected_benefit * 100:.1f}%
是否值得: {'是' if beneficial else '否'}
"""

        return CostBenefitResult(
            single_cost=single_cost,
            multi_cost=multi_cost,
            expected_benefit=expected_benefit,
            beneficial=beneficial,
            reasoning=reasoning.strip()
        )


# 全局单例
_evaluator_instance: Optional[TaskComplexityEvaluator] = None


def get_task_evaluator() -> TaskComplexityEvaluator:
    """获取全局任务评估器实例"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = TaskComplexityEvaluator()
    return _evaluator_instance
