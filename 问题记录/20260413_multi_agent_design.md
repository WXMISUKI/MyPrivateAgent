# MyPrivateAgent 多智能体架构设计方案

## 文档信息
- **创建日期**: 2026-04-13
- **版本**: v2.0
- **状态**: 待评审
- **参考来源**: Claude Code 源码泄露分析、Anthropic Research 多智能体系统

---

## 一、需求概述

### 1.1 新增需求

1. **多智能体模式支持**
   - 添加"多智能体模式"开关
   - 开启后：使用豆包作为主模型，自动spawn子智能体并行处理任务
   - 关闭后：使用当前选择的大模型进行单智能体对话

2. **豆包模型集成**
   - 添加火山引擎豆包模型作为选项
   - 支持通过 API Key 调用
   - 作为多智能体模式的主模型

3. **本地模型在线检测**
   - 检测本地 Ollama 模型是否在线
   - 如果本地模型可用，可以作为子智能体
   - 如果本地模型不可用，豆包自身启动多个子实例

4. **模型选择逻辑**
   - 多智能体模式开启：隐藏模型选择下拉框，强制使用豆包
   - 多智能体模式关闭：显示模型选择，用户可以切换

### 1.2 用户决策确认

| 决策项 | 用户选择 |
|--------|----------|
| **并行度** | 3-5 个子智能体 |
| **子智能体策略** | 豆包自身启动多个子实例 |
| **触发机制** | 用户手动开启 |

---

## 二、Claude Code 多智能体架构研究

### 2.1 核心架构模式

#### 2.1.1 AgentTool 协调器

Claude Code 使用 `AgentTool` 作为多智能体协调器，支持多种执行模式：

```
AgentTool 支持的执行模式：
├── Synchronous subagents  (同步子智能体)
├── Asynchronous agents    (异步智能体)
├── Fork subagents         (继承上下文的子智能体)
├── Teammates              (命名智能体，支持消息路由)
└── Remote agents          (隔离执行的远程智能体)
```

#### 2.1.2 Coordinator-Worker 模式

```
用户查询
    ↓
Lead Agent (主智能体)
    ↓
    ├── 子智能体 1: 任务 A
    ├── 子智能体 2: 任务 B
    ├── 子智能体 3: 任务 C
    └── 子智能体 4: 任务 D
    ↓
结果合并
    ↓
最终响应
```

### 2.2 关键技术要点

#### 2.2.1 KV Cache 共享

**原理**: Fork 子智能体创建父上下文的字节级副本，共享 KV cache

**优势**:
- 并行执行几乎是免费的（token 成本极低）
- 子智能体只处理独特的指令，而非整个共享上下文

**实现思路**:
```python
# Fork 子智能体共享父上下文
def spawn_subagent(parent_context: Context) -> Subagent:
    # 创建字节级相同的上下文副本
    child_context = parent_context.copy_bytes()
    # 共享 KV cache
    child_context.share_kv_cache(parent_context)
    return Subagent(context=child_context)
```

#### 2.2.2 Worktree 隔离

**原理**: 子智能体在隔离的 git worktree 中运行

**优势**:
- 防止并行编辑时的合并冲突
- 提供文件系统级别的隔离

**实现思路**:
```python
def create_worktree_isolation(agent_id: str) -> Worktree:
    slug = f"agent-{agent_id[:8]}"
    worktree_path = create_git_worktree(slug)
    return Worktree(path=worktree_path)
```

#### 2.2.3 邮箱模式（Mailbox Pattern）

**原理**: 危险操作需要发送请求到协调者的邮箱

**优势**:
- 子智能体不能独立批准高风险操作
- 协调者集中控制权限

**实现思路**:
```python
class Mailbox:
    def __init__(self, coordinator: Agent):
        self.coordinator = coordinator
        self.pending_requests = []

    def submit(self, request: DangerousRequest):
        self.pending_requests.append(request)
        # 等待协调者批准
        return self.coordinator.evaluate(request)
```

#### 2.2.4 并行工具调用

**原理**: 子智能体使用多个工具并行执行

**性能提升**: 复杂查询研究时间缩短 90%

**实现思路**:
```python
async def parallel_tool_calls(tools: List[Tool]):
    # 并行调用多个工具
    results = await asyncio.gather(*[
        tool.execute() for tool in tools
    ])
    return results
```

### 2.3 提示工程最佳实践

基于 Anthropic Research 的经验：

1. **思考像智能体一样**
   - 理解智能体如何工作
   - 准确预测行为变化

2. **教导协调者如何委派**
   - 子智能体需要：目标、输出格式、工具指导、任务边界
   - 详细的任务描述避免重复工作和遗漏

3. **按查询复杂度扩展资源**
   - 简单事实查找：1 个智能体，3-10 次工具调用
   - 直接比较：2-4 个子智能体，每个 10-15 次调用
   - 复杂研究：>10 个子智能体，明确分工

4. **工具设计至关重要**
   - 检查所有可用工具
   - 匹配工具使用与用户意图
   - 优先使用专用工具而非通用工具

5. **让智能体自我改进**
   - Claude 4 模型可以是优秀的提示工程师
   - 给定提示和失败模式，诊断原因并建议改进

6. **先宽后窄**
   - 从短、宽泛的查询开始
   - 评估可用内容，然后逐步缩小焦点

7. **引导思维过程**
   - 扩展思维模式作为可控的草稿
   - 主智能体使用思维来规划方法
   - 子智能体使用交错思维来评估质量

---

## 三、多智能体架构设计

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ 登录页面  │  │ 主页面    │  │ 设置页面  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│                     ↓                                        │
│         ┌─────────────────────┐                              │
│         │ 多智能体模式开关     │ ◄── 新增                      │
│         │ 开启: 豆包 + 子智能体 │                              │
│         │ 关闭: 用户选择的模型   │                              │
│         └─────────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   API 路由层 (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 认证路由  │  │ 对话路由  │  │ 会话路由  │  │ 模型路由  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                     ↓                                        │
│         ┌─────────────────────┐                              │
│         │ 模型在线检测 API     │ ◄── 新增                      │
│         └─────────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Agent Orchestrator 层（新增）                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         MultiAgentOrchestrator (多智能体协调器)      │   │
│  │  - 检测多智能体模式是否开启                           │   │
│  │  - 路由到单智能体或多智能体流程                       │   │
│  │  - 管理子智能体生命周期                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Lead     │  │ Subagent │  │ Result   │  │ Model    │    │
│  │ Agent    │  │ Spawner  │  │ Merger   │  │ Detector │    │
│  │ (主智能体)│  │ (子智能体生成器)│  │ (结果合并器)│  │ (模型检测器)│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   模型层（扩展）                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ 豆包模型  │  │Llama 3.1 │  │DeepSeek  │                   │
│  │ (主模型)  │  │ (子智能体)│  │ (子智能体)│                   │
│  │火山引擎   │  │  Ollama  │  │  Ollama  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│  ┌───────────────────────────────────────────────────┐     │
│  │         Model Router (模型路由器)                 │     │
│  │  - 单智能体模式: 使用用户选择的模型                 │     │
│  │  - 多智能体模式: 主模型用豆包，子智能体用豆包子实例  │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   工具层（保持不变）                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 搜索工具  │  │ 时间工具  │  │ Skills   │  │ 扩展工具  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据层                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ MySQL    │  │ 文件系统  │  │ 内存索引  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件设计

#### 3.2.1 MultiAgentOrchestrator（多智能体协调器）

```python
class MultiAgentOrchestrator:
    """多智能体协调器"""

    def __init__(
        self,
        conversation_id: int,
        multi_agent_mode: bool,
        db: Session
    ):
        self.conversation_id = conversation_id
        self.multi_agent_mode = multi_agent_mode
        self.db = db
        self.model_detector = ModelDetector()
        self.model_router = ModelRouter()

    async def process_message(
        self,
        user_message: str,
        selected_model: str = None
    ) -> str:
        """处理用户消息"""

        if self.multi_agent_mode:
            # 多智能体模式：使用豆包作为主模型
            return await self._process_with_multi_agent(user_message)
        else:
            # 单智能体模式：使用用户选择的模型
            model = selected_model or "llama3.1"
            return await self._process_with_single_agent(
                user_message,
                model
            )

    async def _process_with_multi_agent(
        self,
        user_message: str
    ) -> str:
        """多智能体模式处理流程"""

        # 1. 创建主智能体（豆包）
        lead_agent = await self._create_lead_agent()

        # 2. 主智能体分析任务并创建子智能体
        subagent_tasks = await lead_agent.plan_and_spawn(
            user_message,
            max_subagents=5  # 用户选择：3-5 个子智能体
        )

        # 3. 并行执行子智能体
        subagent_results = await self._execute_subagents_parallel(
            subagent_tasks
        )

        # 4. 合并结果
        final_result = await lead_agent.merge_results(
            user_message,
            subagent_results
        )

        return final_result

    async def _process_with_single_agent(
        self,
        user_message: str,
        model: str
    ) -> str:
        """单智能体模式处理流程"""

        # 创建单个智能体
        agent = await self._create_single_agent(model)

        # 直接处理消息
        result = await agent.process(user_message)

        return result

    async def _create_lead_agent(self) -> LeadAgent:
        """创建主智能体（豆包）"""

        model = self.model_router.get_model("main", "doubao")

        return LeadAgent(
            model=model,
            tools=self._get_tools(),
            context_manager=ContextManager()
        )

    async def _execute_subagents_parallel(
        self,
        tasks: List[SubagentTask]
    ) -> List[SubagentResult]:
        """并行执行子智能体"""

        # 使用豆包子实例
        subagents = []
        for task in tasks:
            model = self.model_router.get_model("main", "doubao")
            subagent = Subagent(
                model=model,
                task=task,
                tools=self._get_tools()
            )
            subagents.append(subagent)

        # 并行执行
        results = await asyncio.gather(*[
            subagent.execute() for subagent in subagents
        ])

        return results
```

#### 3.2.2 ModelDetector（模型在线检测器）

```python
class ModelDetector:
    """模型在线检测器"""

    def __init__(self):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.cache: Dict[str, bool] = {}

    async def check_model_online(self, model_name: str) -> bool:
        """检测模型是否在线"""

        # 检查缓存
        if model_name in self.cache:
            return self.cache[model_name]

        try:
            # 调用 Ollama API 检查模型
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ollama_base_url}/api/tags"
                )
                response.raise_for_status()

                data = response.json()
                models = [m["name"] for m in data.get("models", [])]

                is_online = model_name in models
                self.cache[model_name] = is_online

                return is_online

        except Exception as e:
            logger.error(f"检测模型 {model_name} 在线状态失败: {e}")
            self.cache[model_name] = False
            return False

    async def check_all_models(self) -> Dict[str, bool]:
        """检测所有模型在线状态"""

        local_models = ["llama3.1", "deepseek-r1:7b", "llava"]

        results = {}
        for model in local_models:
            results[model] = await self.check_model_online(model)

        return results

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
```

#### 3.2.3 ModelRouter（模型路由器 - 扩展）

```python
class ModelRouter:
    """模型路由器（扩展支持豆包）"""

    def __init__(self):
        self.models = {
            "main": {
                # 豆包模型（新增）
                "doubao": ChatOpenAI(
                    base_url=os.getenv("ARK_BASE_URL"),
                    model=os.getenv("ARK_MODEL", "ep-20250506104302-mj2r7"),
                    api_key=os.getenv("ARK_API_KEY"),
                ),
                # 本地模型
                "llama3.1": ChatOllama(
                    model="llama3.1",
                    base_url=os.getenv("OLLAMA_BASE_URL")
                ),
                "deepseek-r1:7b": ChatOllama(
                    model="deepseek-r1:7b",
                    base_url=os.getenv("OLLAMA_BASE_URL")
                ),
            },
            "safety": {
                "haiku": ChatOllama(
                    model="llama3.1",
                    temperature=0.1,
                    base_url=os.getenv("OLLAMA_BASE_URL")
                ),
            },
            "compression": {
                "haiku": ChatOllama(
                    model="llama3.1",
                    temperature=0.3,
                    base_url=os.getenv("OLLAMA_BASE_URL")
                ),
            }
        }

    def get_model(
        self,
        purpose: str,
        model_name: str = None
    ) -> ChatOpenAI:
        """获取模型"""

        if model_name:
            return self.models["main"][model_name]

        if purpose == "safety":
            return self.models["safety"]["haiku"]
        elif purpose == "compression":
            return self.models["compression"]["haiku"]
        else:
            # 默认返回豆包模型（多智能体模式下）
            return self.models["main"]["doubao"]

    async def check_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""

        if model_name == "doubao":
            # 检查 API Key 是否配置
            return bool(os.getenv("ARK_API_KEY"))
        else:
            # 检查本地模型是否在线
            detector = ModelDetector()
            return await detector.check_model_online(model_name)
```

#### 3.2.4 LeadAgent（主智能体）

```python
class LeadAgent:
    """主智能体（多智能体模式）"""

    def __init__(
        self,
        model: ChatOpenAI,
        tools: List[BaseTool],
        context_manager: ContextManager
    ):
        self.model = model
        self.tools = tools
        self.context_manager = context_manager

    async def plan_and_spawn(
        self,
        user_message: str,
        max_subagents: int = 5
    ) -> List[SubagentTask]:
        """规划任务并生成子智能体"""

        # 1. 分析任务复杂度
        task_analysis = await self._analyze_task(user_message)

        # 2. 确定子智能体数量
        num_subagents = self._determine_subagent_count(
            task_analysis,
            max_subagents
        )

        # 3. 分解任务
        subtasks = await self._decompose_task(
            user_message,
            num_subagents
        )

        # 4. 创建子智能体任务
        subagent_tasks = []
        for i, subtask in enumerate(subtasks):
            task = SubagentTask(
                task_id=f"subagent_{i}",
                description=subtask["description"],
                tools=subtask.get("tools", self.tools),
                output_format=subtask.get("output_format", "text")
            )
            subagent_tasks.append(task)

        return subagent_tasks

    async def _analyze_task(self, user_message: str) -> TaskAnalysis:
        """分析任务复杂度"""

        # 使用扩展思维模式分析
        prompt = f"""
        分析以下任务的复杂度，判断是否需要使用多智能体：

        用户消息: {user_message}

        请分析：
        1. 任务类型（简单事实查找 / 直接比较 / 复杂研究）
        2. 需要的子智能体数量（1-5 个）
        3. 每个子智能体的具体任务
        4. 需要使用的工具

        返回 JSON 格式：
        {{
            "task_type": "simple_fact_finding | direct_comparison | complex_research",
            "num_subagents": 1-5,
            "reasoning": "分析理由",
            "subtasks": [
                {{
                    "description": "子任务描述",
                    "tools": ["tool1", "tool2"],
                    "output_format": "text | json | code"
                }}
            ]
        }}
        """

        response = await self.model.ainvoke(prompt)
        analysis = json.loads(response.content)

        return TaskAnalysis(**analysis)

    def _determine_subagent_count(
        self,
        analysis: TaskAnalysis,
        max_subagents: int
    ) -> int:
        """确定子智能体数量"""

        # 根据任务类型确定子智能体数量
        if analysis.task_type == "simple_fact_finding":
            return min(1, max_subagents)
        elif analysis.task_type == "direct_comparison":
            return min(3, max_subagents)
        elif analysis.task_type == "complex_research":
            return min(5, max_subagents)
        else:
            return min(analysis.num_subagents, max_subagents)

    async def _decompose_task(
        self,
        user_message: str,
        num_subagents: int
    ) -> List[Dict]:
        """分解任务"""

        # 如果只有一个子智能体，直接处理
        if num_subagents == 1:
            return [{
                "description": user_message,
                "tools": self.tools,
                "output_format": "text"
            }]

        # 多个子智能体，分解任务
        prompt = f"""
        将以下任务分解为 {num_subagents} 个子任务，每个子任务由一个子智能体独立处理：

        用户消息: {user_message}

        要求：
        1. 子任务之间应该相互独立，可以并行执行
        2. 每个子任务应该有明确的输出格式
        3. 子任务之间应该互补，覆盖用户请求的所有方面

        返回 JSON 格式：
        {{
            "subtasks": [
                {{
                    "description": "子任务描述",
                    "tools": ["tool1", "tool2"],
                    "output_format": "text | json | code"
                }}
            ]
        }}
        """

        response = await self.model.ainvoke(prompt)
        result = json.loads(response.content)

        return result["subtasks"]

    async def merge_results(
        self,
        user_message: str,
        subagent_results: List[SubagentResult]
    ) -> str:
        """合并子智能体结果"""

        # 构建合并提示
        results_summary = "\n\n".join([
            f"子智能体 {i+1} 结果:\n{result.content}"
            for i, result in enumerate(subagent_results)
        ])

        prompt = f"""
        用户问题: {user_message}

        以下是多个子智能体的研究结果：

        {results_summary}

        请综合以上结果，给出一个完整、准确的回答。
        如果有冲突的信息，请说明并选择最可信的来源。
        如果信息不完整，请明确指出。

        回答要求：
        1. 全面覆盖用户问题
        2. 逻辑清晰，结构合理
        3. 引用子智能体的具体结果
        """

        response = await self.model.ainvoke(prompt)

        return response.content
```

#### 3.2.5 Subagent（子智能体）

```python
class Subagent:
    """子智能体"""

    def __init__(
        self,
        model: ChatOpenAI,
        task: SubagentTask,
        tools: List[BaseTool]
    ):
        self.model = model
        self.task = task
        self.tools = tools

    async def execute(self) -> SubagentResult:
        """执行子智能体任务"""

        try:
            # 1. 构建任务提示
            prompt = self._build_task_prompt()

            # 2. 绑定工具
            model_with_tools = self.model.bind_tools(self.tools)

            # 3. 执行任务（支持工具调用）
            response = await model_with_tools.ainvoke(prompt)

            # 4. 提取结果
            content = response.content

            # 5. 格式化输出
            formatted_result = self._format_output(content)

            return SubagentResult(
                task_id=self.task.task_id,
                content=formatted_result,
                status="success"
            )

        except Exception as e:
            logger.error(f"子智能体 {self.task.task_id} 执行失败: {e}")
            return SubagentResult(
                task_id=self.task.task_id,
                content=f"执行失败: {str(e)}",
                status="failed"
            )

    def _build_task_prompt(self) -> str:
        """构建任务提示"""

        prompt = f"""
        你是一个子智能体，你的任务是：

        {self.task.description}

        可用工具：
        {self._get_tools_description()}

        期望输出格式：{self.task.output_format}

        请独立完成你的任务，不要依赖其他子智能体的结果。
        """

        return prompt

    def _get_tools_description(self) -> str:
        """获取工具描述"""

        descriptions = []
        for tool in self.tools:
            descriptions.append(
                f"- {tool.name}: {tool.description}"
            )
        return "\n".join(descriptions)

    def _format_output(self, content: str) -> str:
        """格式化输出"""

        if self.task.output_format == "json":
            try:
                # 尝试解析为 JSON
                data = json.loads(content)
                return json.dumps(data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                # 如果不是有效 JSON，返回原内容
                return content
        else:
            return content
```

### 3.3 数据模型扩展

#### 3.3.1 多智能体模式配置

```python
# models.py 新增

class Conversation(Base):
    """会话表（扩展）"""
    # ... 现有字段 ...

    # 新增字段
    multi_agent_mode = Column(Boolean, default=False)  # 是否开启多智能体模式


class MultiAgentTask(Base):
    """多智能体任务表（新增）"""
    __tablename__ = "multi_agent_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    task_type = Column(String(50))  # lead / subagent
    task_id = Column(String(100))   # 任务唯一标识
    description = Column(Text)      # 任务描述
    status = Column(String(50))     # pending / running / completed / failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    result = Column(Text)           # 任务结果
    created_at = Column(DateTime, default=datetime.now)
```

#### 3.3.2 Schema 扩展

```python
# schemas.py 新增

class MultiAgentModeRequest(BaseModel):
    """多智能体模式切换请求"""
    conversation_id: int
    enabled: bool


class ModelStatusResponse(BaseModel):
    """模型状态响应"""
    models: Dict[str, bool]  # 模型名 -> 是否在线


class SubagentTask(BaseModel):
    """子智能体任务"""
    task_id: str
    description: str
    tools: List[str] = []
    output_format: str = "text"


class SubagentResult(BaseModel):
    """子智能体结果"""
    task_id: str
    content: str
    status: str  # success / failed


class TaskAnalysis(BaseModel):
    """任务分析结果"""
    task_type: str
    num_subagents: int
    reasoning: str
    subtasks: List[SubagentTask]
```

### 3.4 API 路由扩展

#### 3.4.1 新增 API 端点

```python
# routers/multi_agent.py (新增)

@router.post("/multi-agent/toggle")
def toggle_multi_agent_mode(
    request: MultiAgentModeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """切换多智能体模式"""

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

    # 更新多智能体模式
    conversation.multi_agent_mode = request.enabled
    db.commit()

    return {
        "conversation_id": request.conversation_id,
        "multi_agent_mode": request.enabled,
        "message": f"多智能体模式已{'开启' if request.enabled else '关闭'}"
    }


@router.get("/models/status", response_model=ModelStatusResponse)
def get_models_status():
    """获取所有模型在线状态"""

    model_detector = ModelDetector()
    models_status = asyncio.run(model_detector.check_all_models())

    # 添加豆包模型状态
    models_status["doubao"] = bool(os.getenv("ARK_API_KEY"))

    return ModelStatusResponse(models=models_status)
```

#### 3.4.2 修改现有路由

```python
# routers/chat.py (修改)

@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """流式对话（支持多智能体）"""

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

    # 检查多智能体模式
    if conversation.multi_agent_mode:
        # 多智能体模式
        orchestrator = MultiAgentOrchestrator(
            conversation_id=request.conversation_id,
            multi_agent_mode=True,
            db=db
        )

        return StreamingResponse(
            orchestrator.process_message_stream(request.message),
            media_type="text/event-stream"
        )
    else:
        # 单智能体模式（原有逻辑）
        # ... 原有代码 ...
```

### 3.5 前端修改

#### 3.5.1 添加多智能体模式开关

```html
<!-- index.html 新增 -->

<div class="multi-agent-mode-control">
    <label class="switch">
        <input
            type="checkbox"
            id="multiAgentMode"
            onchange="toggleMultiAgentMode()"
        />
        <span class="slider round"></span>
    </label>
    <span>多智能体模式</span>
</div>

<div class="model-selector" id="modelSelector">
    <!-- 现有的模型选择下拉框 -->
    <select id="modelSelect">
        <option value="llama3.1">Llama 3.1</option>
        <option value="deepseek-r1:7b">DeepSeek R1 7B</option>
        <option value="llava">Llava</option>
    </select>
</div>

<style>
.multi-agent-mode-control {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .4s;
}

.slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .4s;
}

input:checked + .slider {
    background-color: #2196F3;
}

input:checked + .slider:before {
    transform: translateX(26px);
}

.slider.round {
    border-radius: 24px;
}

.slider.round:before {
    border-radius: 50%;
}

#modelSelector.hidden {
    display: none;
}
</style>
```

#### 3.5.2 JavaScript 逻辑

```javascript
// app.js 新增

async function toggleMultiAgentMode() {
    const checkbox = document.getElementById('multiAgentMode');
    const modelSelector = document.getElementById('modelSelector');
    const enabled = checkbox.checked;

    // 隐藏/显示模型选择器
    if (enabled) {
        modelSelector.classList.add('hidden');
    } else {
        modelSelector.classList.remove('hidden');
    }

    // 调用 API 切换模式
    try {
        const response = await fetch(`/api/multi-agent/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                conversation_id: currentConversationId,
                enabled: enabled
            })
        });

        const result = await response.json();
        console.log(result.message);
    } catch (error) {
        console.error('切换多智能体模式失败:', error);
        // 恢复开关状态
        checkbox.checked = !enabled;
        modelSelector.classList.toggle('hidden');
    }
}

// 初始化时检查多智能体模式
async function initMultiAgentMode() {
    try {
        const response = await fetch(`/api/models/status`);
        const result = await response.json();

        // 更新模型状态显示
        console.log('模型状态:', result.models);
    } catch (error) {
        console.error('获取模型状态失败:', error);
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', initMultiAgentMode);
```

### 3.6 环境变量配置

```bash
# .env 新增

# 豆包模型配置
ARK_API_KEY="cab766e7-d21b-4f17-83df-b45c9e891e5a"
ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
ARK_MODEL="ep-20250506104302-mj2r7"  # 豆包模型端点 ID

# Ollama 配置（现有）
OLLAMA_BASE_URL="http://localhost:11434"
```

### 3.7 依赖更新

```txt
# requirements.txt 新增

langchain-openai>=0.2.0  # 豆包模型支持
httpx>=0.27.0  # 异步 HTTP 客户端
```

---

## 四、实现路线图

### 阶段 1: 基础设施准备（优先级：高）

**目标**: 实现模型检测和豆包模型集成

**任务**:
1. 添加豆包模型环境变量配置
2. 实现 `ModelDetector` 模型在线检测器
3. 扩展 `ModelRouter` 支持豆包模型
4. 添加豆包模型 API 调用测试
5. 实现模型状态查询 API

**预期成果**:
- 豆包模型可以正常调用
- 能够检测本地模型在线状态
- 模型状态查询 API 正常工作

**预计时间**: 1-2 天

### 阶段 2: 多智能体核心架构（优先级：高）

**目标**: 实现多智能体协调器和子智能体

**任务**:
1. 实现 `MultiAgentOrchestrator` 多智能体协调器
2. 实现 `LeadAgent` 主智能体
3. 实现 `Subagent` 子智能体
4. 实现任务分解和子智能体 spawning
5. 实现并行执行机制
6. 实现结果合并逻辑

**预期成果**:
- 多智能体协调器能够正常工作
- 主智能体能够分解任务并生成子智能体
- 子智能体能够并行执行
- 结果能够正确合并

**预计时间**: 3-4 天

### 阶段 3: 数据库和 API 扩展（优先级：高）

**目标**: 扩展数据模型和 API 端点

**任务**:
1. 扩展 `Conversation` 表添加多智能体模式字段
2. 创建 `MultiAgentTask` 表
3. 实现多智能体模式切换 API
4. 实现模型状态查询 API
5. 修改聊天 API 支持多智能体模式

**预期成果**:
- 数据库支持多智能体模式
- 多智能体模式可以正常切换
- 聊天 API 支持多智能体和单智能体模式

**预计时间**: 2 天

### 阶段 4: 前端集成（优先级：中）

**目标**: 实现多智能体模式 UI

**任务**:
1. 添加多智能体模式开关
2. 实现模型选择器显示/隐藏逻辑
3. 添加模型状态显示
4. 优化多智能体模式下的聊天体验
5. 添加子智能体执行进度显示

**预期成果**:
- 用户可以方便地切换多智能体模式
- 多智能体模式下 UI 体验良好
- 能够看到子智能体执行进度

**预计时间**: 2 天

### 阶段 5: 测试和优化（优先级：高）

**目标**: 全面测试和性能优化

**任务**:
1. 单元测试（ModelDetector, MultiAgentOrchestrator）
2. 集成测试（完整的多智能体流程）
3. 性能测试（并行执行效率）
4. 错误处理测试（子智能体失败）
5. 优化任务分解逻辑
6. 优化结果合并逻辑

**预期成果**:
- 所有测试用例通过
- 多智能体模式性能良好
- 错误处理完善

**预计时间**: 2-3 天

---

## 五、测试计划

### 5.1 单元测试

```python
# tests/test_model_detector.py

async def test_check_model_online():
    """测试模型在线检测"""
    detector = ModelDetector()

    # 测试在线模型
    result = await detector.check_model_online("llama3.1")
    assert isinstance(result, bool)

    # 测试离线模型
    result = await detector.check_model_online("non_existent_model")
    assert result is False


async def test_check_all_models():
    """测试检测所有模型"""
    detector = ModelDetector()
    results = await detector.check_all_models()

    assert "llama3.1" in results
    assert "deepseek-r1:7b" in results
    assert isinstance(results["llama3.1"], bool)
```

### 5.2 集成测试

```python
# tests/test_multi_agent.py

async def test_multi_agent_mode():
    """测试多智能体模式"""

    orchestrator = MultiAgentOrchestrator(
        conversation_id=1,
        multi_agent_mode=True,
        db=db
    )

    # 测试简单任务
    result = await orchestrator.process_message("你好")
    assert result is not None

    # 测试复杂任务
    result = await orchestrator.process_message(
        "研究 2025 年 AI 智能体的发展趋势"
    )
    assert result is not None
    assert "智能体" in result or "AI" in result


async def test_single_agent_mode():
    """测试单智能体模式"""

    orchestrator = MultiAgentOrchestrator(
        conversation_id=1,
        multi_agent_mode=False,
        db=db
    )

    # 测试单智能体对话
    result = await orchestrator.process_message(
        "你好",
        selected_model="llama3.1"
    )
    assert result is not None
```

### 5.3 性能测试

```python
# tests/test_performance.py

async def test_parallel_execution():
    """测试并行执行性能"""

    orchestrator = MultiAgentOrchestrator(
        conversation_id=1,
        multi_agent_mode=True,
        db=db
    )

    # 测试串行执行
    start_time = time.time()
    result = await orchestrator.process_message(
        "研究 AI、机器学习和深度学习"
    )
    serial_time = time.time() - start_time

    # 测试并行执行
    start_time = time.time()
    result = await orchestrator.process_message(
        "研究 AI、机器学习和深度学习"
    )
    parallel_time = time.time() - start_time

    # 并行执行应该更快
    assert parallel_time < serial_time
```

---

## 六、风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 豆包 API 限流 | 高 | 中 | 实现重试机制，使用本地模型作为备用 |
| 子智能体数量过多 | 中 | 中 | 限制最大子智能体数量（3-5 个） |
| 任务分解不合理 | 高 | 中 | 优化提示工程，增加任务分解验证 |
| 结果合并质量差 | 高 | 中 | 改进合并提示，添加结果验证 |
| 并行执行失败 | 中 | 低 | 完善错误处理，支持子智能体重试 |
| 性能问题 | 中 | 中 | 实现缓存，优化并行调度 |

---

## 七、成功标准

### 7.1 功能标准
- [ ] 多智能体模式开关正常工作
- [ ] 豆包模型可以正常调用
- [ ] 本地模型在线检测准确
- [ ] 主智能体能够正确分解任务
- [ ] 子智能体能够并行执行
- [ ] 结果能够正确合并
- [ ] 单智能体模式不受影响

### 7.2 性能标准
- [ ] 多智能体模式响应时间 < 单智能体模式 × 1.5
- [ ] 子智能体并行执行效率 > 串行执行 × 2
- [ ] 模型在线检测响应时间 < 2 秒

### 7.3 质量标准
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过率 100%
- [ ] 无重大 Bug
- [ ] 代码可维护性良好

---

## 八、下一步行动

1. **评审设计方案**: 请您审阅本方案，提出修改意见
2. **确认技术细节**: 确认豆包模型的具体配置和使用方式
3. **开始实施**: 按照阶段计划开始开发
4. **测试验证**: 每个阶段完成后进行测试

---

## 九、参考资料

1. Claude Code Pattern 7: Multi-Agent Coordination
2. How we built our multi-agent research system - Anthropic
3. 5 ways to spawn Multi Agents with the Claude SDK
4. Multi-Agent System Patterns: Architectures, Roles & Design Guide
5. LangChain 官方文档
6. LangGraph 官方文档
7. 火山引擎豆包模型 API 文档

---

**文档结束**

请审阅此方案，如有任何问题或建议，请随时提出。确认后我将立即开始实施。