# MyPrivateAgent 简化版多智能体架构设计方案

## 文档信息
- **创建日期**: 2026-04-13
- **版本**: v3.0 (简化版)
- **状态**: 待评审
- **参考来源**: Claude Code 源码、企业级多智能体最佳实践、DeepSeek R1 技术文档

---

## 一、需求概述

### 1.1 核心需求

1. **豆包模型集成**
   - API Key: `cab766e7-d21b-4f17-83df-b45c9e891e5a`
   - Base URL: `https://ark.cn-beijing.volces.com/api/v3`
   - Model ID: `doubao-seed-2-0-mini-260215`
   - 无额度限制
   - 支持灵活配置切换

2. **模型输出适配器**
   - 支持有推理链的模型（如 DeepSeek R1）
   - 支持无推理链的模型（如 Llama 3.1、豆包）
   - 自动识别和解析不同格式的输出
   - 可选择显示/隐藏推理过程

3. **多智能体自动触发机制**
   - 不依赖用户手动切换
   - 基于任务复杂度自动决策
   - 考虑成本效益
   - 智能选择单智能体或多智能体模式

4. **简化版实施**
   - 优先实现核心功能
   - 分阶段迭代
   - 每完成一部分记录进度

### 1.2 企业级多智能体触发场景

根据行业最佳实践，多智能体系统应该在以下场景自动触发：

**场景 1: 复杂研究任务**
- 示例：研究 2025 年 AI 智能体的发展趋势
- 触发条件：需要从多个来源收集信息
- 子智能体数量：3-5 个
- 分工：一个收集新闻，一个收集论文，一个收集案例

**场景 2: 多维度比较**
- 示例：比较三个产品的优缺点
- 触发条件：需要并行分析多个对象
- 子智能体数量：3 个
- 分工：每个子智能体分析一个产品

**场景 3: 代码开发任务**
- 示例：开发一个完整的 Web 应用
- 触发条件：需要多个步骤（设计、编码、测试）
- 子智能体数量：2-3 个
- 分工：一个负责设计，一个负责编码，一个负责测试

**场景 4: 简单对话**
- 示例："你好"、"今天天气怎么样"
- 触发条件：单轮对话，简单问题
- 子智能体数量：0（单智能体模式）
- 原因：不值得增加复杂度和成本

---

## 二、简化版架构设计

### 2.1 整体架构图（简化版）

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ 登录页面  │  │ 主页面    │  │ 设置页面  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│                     ↓                                        │
│  ┌───────────────────────────────────────────────────┐     │
│  │ 模型选择器（支持：豆包、Llama 3.1、DeepSeek R1）    │     │
│  │ 推理显示开关（显示/隐藏思考过程）                     │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   API 路由层 (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 认证路由  │  │ 对话路由  │  │ 会话路由  │  │ 模型路由  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                     ↓                                        │
│  ┌───────────────────────────────────────────────────┐     │
│  │ 智能路由器（自动决定单/多智能体）                     │     │
│  │ - 任务复杂度评估                                      │     │
│  │ - 成本效益分析                                        │     │
│  │ - 自动模式切换                                        │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Model Adapter 层（新增）                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         ModelOutputAdapter (模型输出适配器)          │   │
│  │  - 统一不同模型的输出格式                              │   │
│  │  - 提取推理链（reasoning_content）                   │   │
│  │  - 标准化消息结构                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ 豆包适配器│  │ DeepSeek │  │ Llama    │                 │
│  │ 适配器    │  │ 适配器    │  │ 适配器    │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Task Evaluator 层（新增）                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      TaskComplexityEvaluator (任务复杂度评估器)      │   │
│  │  - 分析任务类型                                        │   │
│  │  - 评估子智能体数量                                    │   │
│  │  - 计算预期成本                                        │   │
│  │  - 决定使用模式                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Simplified Agent Orchestrator 层（新增）        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │       SimplifiedOrchestrator (简化协调器)            │   │
│  │  - 路由到单智能体或多智能体                             │   │
│  │  - 任务分解（简单版本）                                 │   │
│  │  - 结果合并（简单版本）                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ 单智能体  │  │ 主智能体  │  │ 子智能体  │                 │
│  │ 模式      │  │ (豆包)    │  │ (豆包子实例)│                │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   模型层（扩展）                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ 豆包模型  │  │DeepSeek  │  │Llama 3.1 │                   │
│  │ (主模型)  │  │ R1       │  │          │                   │
│  │火山引擎   │  │  Ollama  │  │  Ollama  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   工具层（保持不变）                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 搜索工具  │  │ 时间工具  │  │ Skills   │  │ 扩展工具  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

#### 原则 1: 智能触发而非手动切换

**问题**: 用户手动切换多智能体模式不符合企业级应用习惯

**解决方案**: 基于任务复杂度自动决策

```python
class TaskComplexityEvaluator:
    """任务复杂度评估器"""

    def evaluate(self, user_message: str) -> TaskComplexityResult:
        """评估任务复杂度并决定使用模式"""

        # 1. 快速评估（使用小模型）
        quick_assessment = self._quick_assess(user_message)

        # 2. 如果是简单任务，直接返回单智能体
        if quick_assessment.is_simple:
            return TaskComplexityResult(
                mode="single",
                reasoning="简单对话，不需要多智能体"
            )

        # 3. 详细评估（使用主模型）
        detailed_assessment = self._detailed_assess(user_message)

        # 4. 成本效益分析
        cost_benefit = self._cost_benefit_analysis(detailed_assessment)

        # 5. 决定最终模式
        if cost_benefit.beneficial:
            return TaskComplexityResult(
                mode="multi",
                num_subagents=detailed_assessment.recommended_agents,
                reasoning=f"复杂任务：{detailed_assessment.reasoning}，预期收益：{cost_benefit.expected_benefit}"
            )
        else:
            return TaskComplexityResult(
                mode="single",
                reasoning=f"虽然复杂但成本过高，使用单智能体模式"
            )

    def _quick_assess(self, user_message: str) -> QuickAssessment:
        """快速评估（小模型）"""

        # 简单规则
        simple_indicators = [
            len(user_message) < 50,  # 短消息
            "你好" in user_message or "hi" in user_message.lower(),  # 问候
            "谢谢" in user_message or "thank" in user_message.lower(),  # 感谢
            not any(keyword in user_message for keyword in ["研究", "分析", "比较", "开发", "设计"])  # 无复杂关键词
        ]

        is_simple = any(simple_indicators)

        return QuickAssessment(
            is_simple=is_simple,
            confidence=0.9 if is_simple else 0.3
        )

    def _detailed_assess(self, user_message: str) -> DetailedAssessment:
        """详细评估（主模型）"""

        prompt = f"""
        分析以下任务的复杂度：

        任务: {user_message}

        请评估：
        1. 任务类型（简单对话 / 信息查询 / 复杂研究 / 多维比较 / 开发任务）
        2. 是否需要多个智能体并行工作
        3. 推荐的子智能体数量（0-5，0 表示不需要）
        4. 每个子智能体的任务分工

        返回 JSON：
        {{
            "task_type": "任务类型",
            "needs_multi_agent": true/false,
            "recommended_agents": 数量,
            "reasoning": "分析理由"
        }}
        """

        response = self.model.invoke(prompt)
        data = json.loads(response.content)

        return DetailedAssessment(**data)

    def _cost_benefit_analysis(
        self,
        assessment: DetailedAssessment
    ) -> CostBenefitResult:
        """成本效益分析"""

        # 计算成本
        # 单智能体: 10,000 tokens × $0.001/1k tokens = $0.01
        single_cost = 10 * 0.001

        # 多智能体: 10,000 tokens (主) + 3,000 tokens × 3 (子) = 19,000 tokens × $0.001 = $0.019
        multi_cost = (10 + 3 * assessment.recommended_agents) * 0.001

        # 预期收益
        # 简单任务: 0 收益
        # 复杂研究: 提高质量 50%
        # 多维比较: 提高速度 40%
        # 开发任务: 提高效率 60%

        benefit_map = {
            "简单对话": 0,
            "信息查询": 0.1,
            "复杂研究": 0.5,
            "多维比较": 0.4,
            "开发任务": 0.6
        }

        expected_benefit = benefit_map.get(assessment.task_type, 0)

        # 收益是否大于成本增加
        cost_increase = multi_cost - single_cost
        beneficial = expected_benefit > cost_increase * 10  # 收益需要是成本增加的 10 倍

        return CostBenefitResult(
            single_cost=single_cost,
            multi_cost=multi_cost,
            expected_benefit=expected_benefit,
            beneficial=beneficial
        )
```

#### 原则 2: 模型输出标准化

**问题**: 不同模型输出格式不一致（DeepSeek R1 有 reasoning_content，其他模型没有）

**解决方案**: 使用适配器模式统一输出格式

```python
class ModelOutputAdapter:
    """模型输出适配器"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def adapt(self, raw_response: Any) -> StandardizedResponse:
        """适配不同模型的输出为统一格式"""

        if self.model_name.startswith("deepseek"):
            return self._adapt_deepseek(raw_response)
        elif self.model_name.startswith("doubao"):
            return self._adapt_doubao(raw_response)
        else:
            return self._adapt_standard(raw_response)

    def _adapt_deepseek(
        self,
        raw_response: Any
    ) -> StandardizedResponse:
        """适配 DeepSeek R1 输出"""

        # DeepSeek R1 输出格式：
        # {
        #   "choices": [{
        #     "delta": {
        #       "content": "最终答案",
        #       "reasoning_content": "推理过程"
        #     }
        #   }]
        # }

        if hasattr(raw_response, 'choices') and raw_response.choices:
            delta = raw_response.choices[0].delta

            content = getattr(delta, 'content', '')
            reasoning_content = getattr(delta, 'reasoning_content', None)

            return StandardizedResponse(
                content=content,
                reasoning_content=reasoning_content,
                has_reasoning=True,
                model_name=self.model_name
            )

        return StandardizedResponse(
            content=str(raw_response),
            reasoning_content=None,
            has_reasoning=False,
            model_name=self.model_name
        )

    def _adapt_doubao(
        self,
        raw_response: Any
    ) -> StandardizedResponse:
        """适配豆包输出"""

        # 豆包输出格式：标准 OpenAI 格式
        content = getattr(raw_response, 'content', '')

        return StandardizedResponse(
            content=content,
            reasoning_content=None,
            has_reasoning=False,
            model_name=self.model_name
        )

    def _adapt_standard(
        self,
        raw_response: Any
    ) -> StandardizedResponse:
        """适配标准模型输出"""

        content = getattr(raw_response, 'content', str(raw_response))

        return StandardizedResponse(
            content=content,
            reasoning_content=None,
            has_reasoning=False,
            model_name=self.model_name
        )


class StandardizedResponse:
    """标准化响应"""

    def __init__(
        self,
        content: str,
        reasoning_content: Optional[str] = None,
        has_reasoning: bool = False,
        model_name: str = ""
    ):
        self.content = content
        self.reasoning_content = reasoning_content
        self.has_reasoning = has_reasoning
        self.model_name = model_name

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        result = {
            "content": self.content,
            "model": self.model_name
        }

        if self.has_reasoning and self.reasoning_content:
            result["reasoning_content"] = self.reasoning_content

        return result
```

#### 原则 3: 简化多智能体流程

**问题**: 完整的多智能体系统过于复杂

**解决方案**: 实现简化版，只保留核心功能

```python
class SimplifiedOrchestrator:
    """简化协调器"""

    def __init__(
        self,
        conversation_id: int,
        db: Session,
        show_reasoning: bool = False
    ):
        self.conversation_id = conversation_id
        self.db = db
        self.show_reasoning = show_reasoning
        self.task_evaluator = TaskComplexityEvaluator()
        self.model_router = ModelRouter()
        self.output_adapter_registry = {
            "doubao": ModelOutputAdapter("doubao"),
            "deepseek": ModelOutputAdapter("deepseek"),
            "llama": ModelOutputAdapter("llama")
        }

    async def process_message(
        self,
        user_message: str,
        selected_model: str = "doubao"
    ) -> AsyncGenerator[str, None]:
        """处理用户消息（流式输出）"""

        # 1. 评估任务复杂度
        evaluation = await self.task_evaluator.evaluate(user_message)

        # 2. 根据评估结果选择模式
        if evaluation.mode == "single":
            # 单智能体模式
            async for chunk in self._process_single_agent(
                user_message,
                selected_model
            ):
                yield chunk
        else:
            # 多智能体模式
            async for chunk in self._process_multi_agent(
                user_message,
                evaluation.num_subagents
            ):
                yield chunk

    async def _process_single_agent(
        self,
        user_message: str,
        model_name: str
    ) -> AsyncGenerator[str, None]:
        """单智能体模式处理"""

        # 获取模型
        model = self.model_router.get_model("main", model_name)

        # 构建消息
        messages = [HumanMessage(content=user_message)]

        # 调用模型
        response = await model.ainvoke(messages)

        # 适配输出
        adapter = self.output_adapter_registry.get(
            model_name,
            self.output_adapter_registry["llama"]
        )
        standardized = adapter.adapt(response)

        # 流式输出
        if self.show_reasoning and standardized.has_reasoning:
            # 显示推理过程
            yield f"🤔 思考过程:\n{standardized.reasoning_content}\n\n"
            yield f"🤖 回答:\n{standardized.content}"
        else:
            # 只显示答案
            yield standardized.content

    async def _process_multi_agent(
        self,
        user_message: str,
        num_subagents: int
    ) -> AsyncGenerator[str, None]:
        """多智能体模式处理（简化版）"""

        # 1. 创建主智能体（豆包）
        lead_model = self.model_router.get_model("main", "doubao")

        # 2. 主智能体分解任务（简化版：使用模板）
        subtasks = await self._simple_task_decomposition(
            user_message,
            num_subagents,
            lead_model
        )

        # 3. 并行执行子智能体
        subagent_results = await self._execute_subagents_parallel(
            subtasks
        )

        # 4. 主智能体合并结果
        final_result = await self._merge_results(
            user_message,
            subagent_results,
            lead_model
        )

        # 5. 流式输出
        yield final_result

    async def _simple_task_decomposition(
        self,
        user_message: str,
        num_subagents: int,
        model: Any
    ) -> List[Subtask]:
        """简单任务分解（简化版）"""

        if num_subagents == 1:
            return [Subtask(
                id="subtask_1",
                description=user_message
            )]

        # 使用简单模板分解
        prompt = f"""
        将以下任务分解为 {num_subagents} 个独立的子任务：

        {user_message}

        要求：
        1. 每个子任务应该可以独立完成
        2. 子任务之间不要有依赖关系
        3. 子任务应该互补，覆盖任务的所有方面

        返回 JSON：
        {{
            "subtasks": [
                {{"id": "1", "description": "子任务描述"}},
                ...
            ]
        }}
        """

        response = await model.ainvoke([HumanMessage(content=prompt)])
        data = json.loads(response.content)

        return [
            Subtask(
                id=f"subtask_{i+1}",
                description=task["description"]
            )
            for i, task in enumerate(data["subtasks"])
        ]

    async def _execute_subagents_parallel(
        self,
        subtasks: List[Subtask]
    ) -> List[SubagentResult]:
        """并行执行子智能体"""

        # 创建子智能体任务
        tasks = []
        for subtask in subtasks:
            model = self.model_router.get_model("main", "doubao")
            task = self._execute_single_subagent(subtask, model)
            tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks)

        return results

    async def _execute_single_subagent(
        self,
        subtask: Subtask,
        model: Any
    ) -> SubagentResult:
        """执行单个子智能体"""

        try:
            response = await model.ainvoke([HumanMessage(content=subtask.description)])

            adapter = self.output_adapter_registry["doubao"]
            standardized = adapter.adapt(response)

            return SubagentResult(
                subtask_id=subtask.id,
                content=standardized.content,
                status="success"
            )
        except Exception as e:
            return SubagentResult(
                subtask_id=subtask.id,
                content=f"执行失败: {str(e)}",
                status="failed"
            )

    async def _merge_results(
        self,
        user_message: str,
        results: List[SubagentResult],
        model: Any
    ) -> str:
        """合并结果"""

        # 构建合并提示
        results_text = "\n\n".join([
            f"子任务 {result.subtask_id}:\n{result.content}"
            for result in results
        ])

        prompt = f"""
        用户问题: {user_message}

        以下是多个子智能体的研究结果：

        {results_text}

        请综合以上结果，给出一个完整、准确的回答。
        如果有冲突的信息，请说明并选择最可信的来源。
        如果信息不完整，请明确指出。
        """

        response = await model.ainvoke([HumanMessage(content=prompt)])

        adapter = self.output_adapter_registry["doubao"]
        standardized = adapter.adapt(response)

        return standardized.content
```

---

## 三、技术实现

### 3.1 环境变量配置

```bash
# .env

# 豆包模型配置
ARK_API_KEY="cab766e7-d21b-4f17-83df-b45c9e891e5a"
ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
ARK_MODEL="doubao-seed-2-0-mini-260215"

# Ollama 配置
OLLAMA_BASE_URL="http://localhost:11434"

# 其他配置
DEFAULT_MODEL="doubao"
SHOW_REASONING=false  # 是否显示推理过程
```

### 3.2 数据模型

```python
# models.py

class Conversation(Base):
    """会话表（扩展）"""
    # ... 现有字段 ...

    # 新增字段
    selected_model = Column(String(100), default="doubao")  # 用户选择的模型
    show_reasoning = Column(Boolean, default=False)  # 是否显示推理过程


class TaskEvaluation(Base):
    """任务评估表（新增）"""
    __tablename__ = "task_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    user_message = Column(Text)
    task_type = Column(String(50))  # simple / research / comparison / development
    recommended_mode = Column(String(50))  # single / multi
    recommended_agents = Column(Integer, default=0)
    actual_mode = Column(String(50))  # 实际使用的模式
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
```

### 3.3 Schema 定义

```python
# schemas.py

class TaskComplexityResult(BaseModel):
    """任务复杂度评估结果"""
    mode: Literal["single", "multi"]
    num_subagents: int = 0
    reasoning: str


class StandardizedResponse(BaseModel):
    """标准化响应"""
    content: str
    reasoning_content: Optional[str] = None
    has_reasoning: bool = False
    model_name: str


class Subtask(BaseModel):
    """子任务"""
    id: str
    description: str


class SubagentResult(BaseModel):
    """子智能体结果"""
    subtask_id: str
    content: str
    status: str  # success / failed


class ChatRequestV2(BaseModel):
    """聊天请求（扩展）"""
    model_config = ConfigDict(protected_namespaces=())

    conversation_id: int
    message: str
    model_name: Optional[str] = "doubao"
    show_reasoning: Optional[bool] = False


class ModelInfoV2(BaseModel):
    """模型信息（扩展）"""
    name: str
    display_name: str
    type: Literal["cloud", "local"]
    has_reasoning: bool  # 是否支持推理链
    online: bool  # 是否在线
```

### 3.4 API 路由

```python
# routers/chat.py (修改)

@router.post("/chat/v2")
def chat_v2(
    request: ChatRequestV2,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """流式对话（简化版多智能体）"""

    # 验证会话归属
    conversation = db.query(Conversation).filter(
        Conversation.id == request.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 更新会话配置
    conversation.selected_model = request.model_name or "doubao"
    conversation.show_reasoning = request.show_reasoning
    db.commit()

    # 创建协调器
    orchestrator = SimplifiedOrchestrator(
        conversation_id=request.conversation_id,
        db=db,
        show_reasoning=request.show_reasoning
    )

    # 流式响应
    return StreamingResponse(
        orchestrator.process_message(
            request.message,
            request.model_name or "doubao"
        ),
        media_type="text/event-stream"
    )


@router.get("/models/v2", response_model=List[ModelInfoV2])
def get_models_v2():
    """获取所有模型信息（扩展）"""

    models = [
        {
            "name": "doubao",
            "display_name": "豆包 (火山引擎)",
            "type": "cloud",
            "has_reasoning": False,
            "online": bool(os.getenv("ARK_API_KEY"))
        },
        {
            "name": "deepseek-r1:7b",
            "display_name": "DeepSeek R1 7B",
            "type": "local",
            "has_reasoning": True,
            "online": False  # 需要检测
        },
        {
            "name": "llama3.1",
            "display_name": "Llama 3.1",
            "type": "local",
            "has_reasoning": False,
            "online": False  # 需要检测
        }
    ]

    # 检测本地模型在线状态
    detector = ModelDetector()
    for model in models:
        if model["type"] == "local":
            model["online"] = asyncio.run(
                detector.check_model_online(model["name"])
            )

    return models
```

### 3.5 前端修改

```html
<!-- index.html 修改 -->

<div class="model-control-panel">
    <div class="model-selector">
        <label>选择模型:</label>
        <select id="modelSelect">
            <option value="doubao">豆包 (火山引擎)</option>
            <option value="deepseek-r1:7b">DeepSeek R1 7B</option>
            <option value="llama3.1">Llama 3.1</option>
        </select>
        <span class="model-status" id="modelStatus">●</span>
    </div>

    <div class="reasoning-toggle" id="reasoningToggle">
        <label class="switch">
            <input type="checkbox" id="showReasoning" />
            <span class="slider round"></span>
        </label>
        <span>显示思考过程</span>
    </div>
</div>

<style>
.model-control-panel {
    display: flex;
    gap: 20px;
    margin-bottom: 10px;
    align-items: center;
}

.model-selector {
    display: flex;
    align-items: center;
    gap: 10px;
}

.model-status {
    font-size: 20px;
}

.model-status.online {
    color: #4CAF50;
}

.model-status.offline {
    color: #f44336;
}

.reasoning-toggle {
    display: flex;
    align-items: center;
    gap: 10px;
}
</style>
```

```javascript
// app.js 修改

// 初始化模型状态
async function initModels() {
    try {
        const response = await fetch('/api/models/v2');
        const models = await response.json();

        const select = document.getElementById('modelSelect');
        select.innerHTML = '';

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = `${model.display_name} ${model.online ? '✓' : '✗'}`;

            if (!model.online) {
                option.disabled = true;
            }

            select.appendChild(option);
        });

        // 更新状态指示器
        updateModelStatus();
    } catch (error) {
        console.error('获取模型列表失败:', error);
    }
}

function updateModelStatus() {
    const select = document.getElementById('modelSelect');
    const status = document.getElementById('modelStatus');

    const selectedModel = select.value;

    // 检查是否在线
    const option = select.querySelector(`option[value="${selectedModel}"]`);
    if (option.disabled) {
        status.className = 'model-status offline';
    } else {
        status.className = 'model-status online';
    }
}

// 监听模型切换
document.getElementById('modelSelect').addEventListener('change', updateModelStatus);

// 监听推理显示切换
document.getElementById('showReasoning').addEventListener('change', function() {
    // 保存用户偏好
    localStorage.setItem('showReasoning', this.checked);
});

// 加载用户偏好
document.addEventListener('DOMContentLoaded', () => {
    const showReasoning = localStorage.getItem('showReasoning') === 'true';
    document.getElementById('showReasoning').checked = showReasoning;

    initModels();
});

// 发送消息时带上配置
async function sendMessage() {
    const message = document.getElementById('messageInput').value;
    const selectedModel = document.getElementById('modelSelect').value;
    const showReasoning = document.getElementById('showReasoning').checked;

    const response = await fetch('/api/chat/v2', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            conversation_id: currentConversationId,
            message: message,
            model_name: selectedModel,
            show_reasoning: showReasoning
        })
    });

    // 处理流式响应...
}
```

---

## 四、简化版实施路线图

### 阶段 1: 基础设施（优先级：高）

**目标**: 实现豆包模型集成和模型输出适配器

**任务**:
1. ✅ 添加豆包模型环境变量配置
2. ✅ 实现 `ModelRouter` 支持豆包模型
3. ✅ 实现 `ModelOutputAdapter` 模型输出适配器
4. ✅ 测试豆包模型调用
5. ✅ 测试不同模型的输出适配

**验收标准**:
- [ ] 豆包模型可以正常调用
- [ ] 不同模型的输出可以统一处理
- [ ] DeepSeek R1 的推理链可以正确提取

**预计时间**: 1 天

### 阶段 2: 智能触发机制（优先级：高）

**目标**: 实现任务复杂度评估和自动触发

**任务**:
1. ✅ 实现 `TaskComplexityEvaluator` 任务复杂度评估器
2. ✅ 实现快速评估（小模型）
3. ✅ 实现详细评估（主模型）
4. ✅ 实现成本效益分析
5. ✅ 测试不同任务的评估准确性

**验收标准**:
- [ ] 简单对话自动选择单智能体
- [ ] 复杂任务自动选择多智能体
- [ ] 评估逻辑合理准确

**预计时间**: 2 天

### 阶段 3: 简化协调器（优先级：高）

**目标**: 实现简化版多智能体协调器

**任务**:
1. ✅ 实现 `SimplifiedOrchestrator` 简化协调器
2. ✅ 实现简单任务分解
3. ✅ 实现子智能体并行执行
4. ✅ 实现结果合并
5. ✅ 流式输出支持

**验收标准**:
- [ ] 单智能体模式正常工作
- [ ] 多智能体模式正常工作
- [ ] 流式输出流畅

**预计时间**: 2 天

### 阶段 4: 前端集成（优先级：中）

**目标**: 实现模型选择和推理显示 UI

**任务**:
1. ✅ 实现模型选择下拉框
2. ✅ 实现模型在线状态显示
3. ✅ 实现推理显示开关
4. ✅ 优化聊天体验

**验收标准**:
- [ ] 用户可以选择模型
- [ ] 可以看到模型在线状态
- [ ] 可以切换推理显示

**预计时间**: 1 天

### 阶段 5: 测试和优化（优先级：高）

**目标**: 全面测试和性能优化

**任务**:
1. ✅ 单元测试
2. ✅ 集成测试
3. ✅ 性能测试
4. ✅ 用户体验优化

**验收标准**:
- [ ] 所有测试通过
- [ ] 响应时间合理
- [ ] 用户体验良好

**预计时间**: 1-2 天

---

## 五、预计时间表

| 阶段 | 任务 | 预计时间 | 实际时间 | 状态 |
|------|------|----------|----------|------|
| 1 | 基础设施（豆包集成、输出适配器） | 1 天 | - | ⚪ 未开始 |
| 2 | 智能触发机制（任务评估） | 2 天 | - | ⚪ 未开始 |
| 3 | 简化协调器（多智能体核心） | 2 天 | - | ⚪ 未开始 |
| 4 | 前端集成（UI 优化） | 1 天 | - | ⚪ 未开始 |
| 5 | 测试和优化 | 1-2 天 | - | ⚪ 未开始 |

**总预计时间**: 7-8 天

---

## 六、风险和缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 豆包 API 兼容性问题 | 高 | 充分测试，参考 OpenAI 兼容格式 |
| 任务评估不准确 | 中 | 优化提示工程，增加规则辅助 |
| 多智能体性能问题 | 中 | 限制子智能体数量（3-5 个） |
| 推理链解析失败 | 低 | 多种模型测试，异常处理 |
| 成本超预期 | 低 | 实施成本监控，限制使用 |

---

## 七、成功标准

### 功能标准
- [ ] 豆包模型可以正常调用
- [ ] 可以选择不同模型
- [ ] 可以显示/隐藏推理过程
- [ ] 简单任务自动使用单智能体
- [ ] 复杂任务自动使用多智能体
- [ ] 子智能体并行执行
- [ ] 结果正确合并

### 性能标准
- [ ] 简单任务响应时间 < 3 秒
- [ ] 复杂任务响应时间 < 10 秒
- [ ] 模型在线检测 < 2 秒

### 质量标准
- [ ] 核心功能测试通过率 100%
- [ ] 用户体验流畅
- [ ] 代码可维护

---

## 八、下一步行动

**请确认以下事项后，我将立即开始实施**：

1. **豆包模型配置确认**:
   - API Key: `cab766e7-d21b-4f17-83df-b45c9e891e5a` ✅
   - Base URL: `https://ark.cn-beijing.volces.com/api/v3` ✅
   - Model ID: `doubao-seed-2-0-mini-260215` ✅

2. **简化版范围确认**:
   - 只实现核心功能 ✅
   - 分阶段迭代 ✅
   - 每完成一部分记录进度 ✅

3. **优先级确认**:
   - 阶段 1: 基础设施 ✅
   - 阶段 2: 智能触发 ✅
   - 阶段 3: 简化协调器 ✅
   - 阶段 4: 前端集成 ✅
   - 阶段 5: 测试优化 ✅

**确认后我将按照阶段 1 → 阶段 5 的顺序实施，每完成一个阶段在项目进度文档中记录。**

---

**文档结束**

请审阅此方案，如有任何问题或建议，请随时提出。确认后我将立即开始实施。