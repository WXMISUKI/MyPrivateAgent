# MyPrivateAgent 框架完善总体方案

## 文档信息
- **创建日期**: 2026-04-17
- **版本**: v1.0
- **状态**: 待评审
- **参考来源**: Claude Code 源码泄露分析、企业级智能体最佳实践

---

## 一、总体目标

基于 Claude Code 等成熟智能体的最佳实践，系统性完善 MyPrivateAgent 框架，优先级排序为：

1. 🔴 **高优先级**：思考过程展示、真正工具调用、上下文管理
2. 🟡 **中优先级**：权限管理、错误处理增强、内存管理
3. 🟢 **低优先级**：自我学习、前端优化

---

## 二、高优先级方案

### 2.1 思考过程展示

**详细方案**: 见 `20260417_thinking_display_design.md`

**核心要点**:
- 思考过程与最终答案分离展示
- 折叠面板设计，默认展开
- 支持 Markdown 渲染
- 兼容所有模型

**预计时间**: 1-2 天

---

### 2.2 真正工具调用

#### 2.2.1 当前问题

- Skills 注入到提示词，模型被动接收
- 模型无法真正理解何时调用工具
- "你好"也会提及 Skills

#### 2.2.2 解决方案

使用 LangChain 的 `bind_tools` 实现真正的工具调用：

```python
# 工具定义示例
from langchain_core.tools import tool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str

@tool(args_schema=SearchInput)
def search(query: str) -> str:
    """搜索信息，特别是天气查询"""
    if "上海" in query or "shanghai" in query.lower():
        return "上海现在30度，多云。"
    return "信息未找到"

class DateTimeInput(BaseModel)

@tool
def get_current_datetime() -> str:
    """获取当前日期和时间"""
    from datetime import datetime
    import pytz
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

# 工具注册
tools = [search, get_current_datetime]

# Agent Loop 实现
class AgentHarness:
    def __init__(self, model, tools):
        self.model = model.bind_tools(tools)
        self.tools = {t.name: t for t in tools}

    async def run(self, messages):
        while True:
            # 1. 生成响应
            response = await self.model.ainvoke(messages)

            # 2. 检查工具调用
            if not response.tool_calls:
                return response.content

            # 3. 执行工具
            for tool_call in response.tool_calls:
                result = self.tools[tool_call.name].invoke(tool_call.args)
                messages.append(ToolMessage(
                    content=result,
                    tool_call_id=tool_call.id
                ))
```

#### 2.2.3 实施计划

| 任务 ID | 任务名称 | 预计时间 |
|---------|----------|----------|
| 2.2.1 | 定义基础工具（Search、DateTime） | 2 小时 |
| 2.2.2 | 实现 Skills 工具加载器 | 3 小时 |
| 2.2.3 | 重构 Agent Loop | 4 小时 |
| 2.2.4 | 集成测试 | 2 小时 |

**预计时间**: 3-5 天

#### 2.2.4 验收标准

- [ ] 模型能正确识别何时调用工具
- [ ] 工具执行结果正确返回
- [ ] "你好"不再提及 Skills
- [ ] 豆包、DeepSeek R1、Llama 3.1 均支持

---

### 2.3 上下文管理

#### 2.3.1 当前问题

- 长对话会导致上下文溢出
- 无压缩策略
- 性能随对话增长而下降

#### 2.3.2 解决方案

实现三层压缩策略：

```python
class ContextManager:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    async def compress(self, messages: list) -> list:
        """三层压缩策略"""

        # 层1: MicroCompact - 本地修剪工具输出
        messages = await self._micro_compact(messages)

        # 层2: AutoCompact - 模型生成摘要
        if self._estimate_tokens(messages) > self.max_tokens * 0.8:
            messages = await self._auto_compact(messages)

        # 层3: FullCompact - 完全压缩
        if self._estimate_tokens(messages) > self.max_tokens * 0.95:
            messages = await self._full_compact(messages)

        return messages

    async def _micro_compact(self, messages: list) -> list:
        """本地修剪：移除过长内容"""
        for msg in messages:
            if hasattr(msg, 'content') and len(msg.content) > 2000:
                msg.content = msg.content[:2000] + "...[已截断]"
        return messages

    async def _auto_compact(self, messages: list) -> list:
        """模型摘要：保留最近 N 条，压缩历史"""
        recent = messages[-10:]
        old = messages[:-10]

        # 使用模型生成摘要
        summary = await self._generate_summary(old)
        return [
            SystemMessage(content=f"之前对话摘要: {summary}"),
            *recent
        ]

    async def _full_compact(self, messages: list) -> list:
        """完全压缩：只保留关键信息"""
        # 只保留最近 5 条完整消息
        return messages[-5:]
```

#### 2.3.3 实施计划

| 任务 ID | 任务名称 | 预计时间 |
|---------|----------|----------|
| 2.3.1 | 实现 ContextManager | 3 小时 |
| 2.3.2 | 实现三层压缩策略 | 4 小时 |
| 2.3.3 | 集成到 Agent Loop | 2 小时 |
| 2.3.4 | 测试长对话 | 2 小时 |

**预计时间**: 2-3 天

#### 2.3.4 验收标准

- [ ] 支持 50+ 轮对话不溢出
- [ ] 压缩后保留关键信息
- [ ] Token 使用可监控

---

## 三、中优先级方案

### 3.1 权限管理

#### 3.1.1 问题

- 工具调用无权限检查
- 危险操作无确认机制
- 安全风险

#### 3.1.2 解决方案

```python
from enum import Enum

class PermissionLevel(Enum):
    AUTO = "auto"      # 自动批准
    ASK = "ask"        # 需要用户确认
    DENY = "deny"      # 拒绝执行

class PermissionManager:
    def __init__(self):
        self.tool_permissions = {
            "search": PermissionLevel.AUTO,
            "get_current_datetime": PermissionLevel.AUTO,
            "load_skill": PermissionLevel.ASK,
            "execute_code": PermissionLevel.DENY,
        }

    async def check(self, tool_name: str, args: dict) -> PermissionResult:
        """检查工具调用权限"""
        level = self.tool_permissions.get(tool_name, PermissionLevel.ASK)

        if level == PermissionLevel.AUTO:
            return PermissionResult(allowed=True)

        if level == PermissionLevel.DENY:
            return PermissionResult(allowed=False, reason="危险操作被拒绝")

        # ASK: 需要用户确认
        return PermissionResult(
            allowed=None,  # 待确认
            requires_confirmation=True,
            message=f"是否允许执行 {tool_name}?"
        )
```

#### 3.1.3 实施计划

| 任务 ID | 任务名称 | 预计时间 |
|---------|----------|----------|
| 3.1.1 | 定义权限级别 | 2 小时 |
| 3.1.2 | 实现 PermissionManager | 3 小时 |
| 3.1.3 | 前端确认对话框 | 2 小时 |
| 3.1.4 | 安全测试 | 2 小时 |

**预计时间**: 2-3 天

---

### 3.2 错误处理增强

#### 3.2.1 问题

- 工具调用失败无处理
- 模型异常无重试
- 用户体验差

#### 3.2.2 解决方案

```python
class ErrorHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def execute_with_retry(self, func, *args, **kwargs):
        """带重试的执行"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except ToolExecutionError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue

                # 最终失败，返回友好错误
                return ErrorResult(
                    success=False,
                    message=f"工具执行失败: {str(e)}",
                    recoverable=False
                )

        return ErrorResult(
            success=False,
            message=str(last_error),
            recoverable=True,
            suggestion="请稍后重试或尝试其他方式"
        )
```

#### 3.2.3 实施计划

| 任务 ID | 任务名称 | 预计时间 |
|---------|----------|----------|
| 3.2.1 | 实现 ErrorHandler | 2 小时 |
| 3.2.2 | 集成到 Agent Loop | 2 小时 |
| 3.2.3 | 前端错误展示优化 | 1 小时 |

**预计时间**: 1-2 天

---

### 3.3 内存管理

#### 3.3.1 问题

- 无长期记忆机制
- 无法积累知识
- 每次对话从零开始

#### 3.3.2 解决方案

```python
import os

class MemoryManager:
    def __init__(self, memory_dir: str = "memories"):
        self.memory_dir = memory_dir
        self.index_file = os.path.join(memory_dir, "MEMORY.md")
        os.makedirs(memory_dir, exist_ok=True)

    async def store(self, key: str, content: str):
        """存储记忆"""
        # 保存到文件
        memory_file = os.path.join(self.memory_dir, f"{key}.md")
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # 更新索引
        await self._update_index(key, content[:100])

    async def retrieve(self, key: str) -> Optional[str]:
        """检索记忆"""
        memory_file = os.path.join(self.memory_dir, f"{key}.md")
        if not os.path.exists(memory_file):
            return None

        with open(memory_file, 'r', encoding='utf-8') as f:
            return f.read()

    async def search(self, query: str) -> List[MemoryItem]:
        """搜索记忆"""
        # 简单实现：搜索索引文件
        results = []
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if query.lower() in line.lower():
                        key = line.split(':')[0].strip('- ')
                        content = await self.retrieve(key)
                        results.append(MemoryItem(key=key, content=content))
        return results
```

#### 3.3.3 实施计划

| 任务 ID | 任务名称 | 预计时间 |
|---------|----------|----------|
| 3.3.1 | 实现 MemoryManager | 3 小时 |
| 3.3.2 | 实现记忆索引 | 2 小时 |
| 3.3.3 | 集成到 Agent | 2 小时 |

**预计时间**: 2-3 天

---

## 四、低优先级方案

### 4.1 自我学习

详细设计见 `20260413_self_improvement_design.md`

**预计时间**: 待定

---

### 4.2 前端优化

#### 4.2.1 功能列表

- 工具调用可视化
- 调试模式
- 性能监控面板

#### 4.2.2 实施计划

| 任务 ID | 任务名称 | 预计时间 |
|---------|----------|----------|
| 4.2.1 | 工具调用可视化 | 2 小时 |
| 4.2.2 | 调试模式 | 2 小时 |
| 4.2.3 | 性能监控 | 2 小时 |

**预计时间**: 1-2 天

---

## 五、实施路线图

### 5.1 整体时间估算

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| 阶段1 | 思考过程展示 | 1-2 天 |
| 阶段2 | 真正工具调用 | 3-5 天 |
| 阶段3 | 上下文管理 | 2-3 天 |
| 阶段4 | 权限管理 | 2-3 天 |
| 阶段5 | 错误处理增强 | 1-2 天 |
| 阶段6 | 内存管理 | 2-3 天 |
| 阶段7 | 前端优化 | 1-2 天 |

**总预计时间**: 12-20 天

### 5.2 推荐实施顺序

```
阶段1（1-2天）
    ↓
阶段2（3-5天）
    ↓
阶段3（2-3天）
    ↓
阶段4-7（可选，根据需求）
```

---

## 六、成功标准

### 6.1 功能标准

- [ ] 思考过程展示正常（展开/收缩）
- [ ] 工具调用正常工作
- [ ] 长对话不溢出
- [ ] 权限管理生效
- [ ] 错误处理完善

### 6.2 性能标准

- [ ] 响应时间 < 3 秒
- [ ] 支持 50+ 轮对话
- [ ] 内存占用 < 500MB

### 6.3 质量标准

- [ ] 测试覆盖率 > 80%
- [ ] 无重大 Bug
- [ ] 文档完整

---

## 七、下一步行动

1. **评审本方案**: 请审阅并提出修改意见
2. **确认优先级**: 确认是否按此顺序实施
3. **开始阶段1**: 思考过程展示

---

**文档结束**

请审阅此方案，确认后我将按计划开始实施。
