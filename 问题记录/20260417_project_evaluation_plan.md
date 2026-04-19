# MyPrivateAgent 项目评估与重构方案

## 文档信息
- **创建日期**: 2026-04-17
- **版本**: v1.0
- **状态**: 待评审
- **优先级**: 🔴 高

---

## 一、当前项目状态评估

### 1.1 已实现功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 用户认证 | ✅ 正常 | JWT + HTTPOnly Cookie |
| 多模型支持 | ✅ 正常 | 豆包、Llama、DeepSeek、LLaVA |
| 流式输出 | ✅ 正常 | SSE 实时推送 |
| 会话管理 | ✅ 正常 | 创建、切换、删除会话 |
| 对话历史 | ✅ 正常 | 数据库存储 |
| 思考过程展示 | ⚠️ 部分实现 | 有框架但不稳定 |

### 1.2 当前问题

| 问题 | 严重程度 | 原因 |
|------|----------|------|
| DeepSeek R1 重复输出 | 🔴 高 | Ollama 返回格式特殊处理缺失 |
| 思考动画不显示 | 🟡 中 | reasoning 提取逻辑问题 |
| 多智能体流程臃肿 | 🟡 中 | 已简化但仍可优化 |
| 上下文管理缺失 | 🟡 中 | 长对话会溢出 |

### 1.3 与 Claude Code 差距

| 方面 | Claude Code | 我们 | 差距 |
|------|-------------|------|------|
| 架构 | 6层清晰架构 | 混合架构 | 中 |
| 工具调用 | 真正 Tool Call | 提示词注入 | 大 |
| 上下文管理 | 智能压缩 | 无 | 大 |
| 流式渲染 | 自研 Ink 引擎 | 前端简单处理 | 中 |
| 思考展示 | 结构化分离 | 不稳定 | 中 |

---

## 二、问题根因分析

### 2.1 DeepSeek R1 重复问题

**原因**：Ollama 对 DeepSeek R1 的流式输出处理特殊

Claude Code 的做法：
```
思考过程 → 独立流式输出 → 前端实时展示
最终答案 → 独立流式输出 → 前端实时展示
```

我们的做法（问题）：
```
混合输出 → 前端难以区分 → 重复渲染
```

**解决方案**：
1. 方案A：前端根据模型类型处理（快速修复）
2. 方案B：后端 Ollama 适配器（正确方案）

### 2.2 思考动画不显示

**原因**：
1. DeepSeek R1 的 reasoning 内容格式不是 `<reasoning>` 标签
2. `_extract_reasoning` 方法没有正确提取

**解决方案**：
参考 Claude Code，在模型适配器层统一处理

---

## 三、重构方案

### 3.1 方案A：快速修复（1-2天）

**思路**：针对当前问题打补丁

| 任务 | 内容 |
|------|------|
| 修复 DeepSeek R1 重复 | 前端根据模型类型去重 |
| 修复思考动画 | 检查 reasoning 提取逻辑 |
| 简化评估器 | 移除不必要的评估逻辑 |

**优点**：
- 快速见效
- 改动小

**缺点**：
- 技术债务积累
- 后续维护困难

### 3.2 方案B：参考 Claude Code 重构（5-7天）

**思路**：参考 Claude Code 的分层架构重新设计

```
用户交互层（前端）
    ↓
命令与技能层（Skills）
    ↓
核心引擎层（Agent Loop）
    ↓
模型适配层（Ollama/豆包适配器）
    ↓
服务层（LangChain/LangGraph）
```

**核心改进**：
1. 清晰的模型适配器层
2. 真正的 Agent Loop
3. 智能上下文管理
4. 统一的流式输出处理

**优点**：
- 架构清晰
- 易于维护
- 真正学习 Claude Code

**缺点**：
- 改动大
- 需要时间

---

## 四、Claude Code 核心架构参考

### 4.1 六层架构

```
┌─────────────────────────────────────┐
│ 用户交互层（Ink 渲染引擎）            │
├─────────────────────────────────────┤
│ 命令与技能层（内建命令 + 可扩展 Skills）│
├─────────────────────────────────────┤
│ 核心引擎层（Agent Loop + Planning）   │
├─────────────────────────────────────┤
│ 服务层（LangGraph + Tools）          │
├─────────────────────────────────────┤
│ 通信层（SSE + A2A）                  │
├─────────────────────────────────────┤
│ 基础设施层（数据库 + 配置）           │
└─────────────────────────────────────┘
```

### 4.2 Agent Loop 参考

```python
class AgentLoop:
    async def run(self, user_message):
        while True:
            # 1. 思考（规划）
            thought = await self planner.think(user_message, context)

            # 2. 行动（执行工具或生成答案）
            action = await self.planner.decide(thought)

            if action.is_answer:
                return action.result  # 最终答案
            elif action.is_tool_call:
                result = await self.tools.execute(action.tool)
                context.add(result)  # 添加到上下文
            else:
                continue  # 继续循环
```

### 4.3 流式输出参考

```python
async def stream_response(user_message):
    # 思考过程流
    async for thought in agent.think_stream(user_message):
        yield f"data: {{'type': 'thought', 'content': '{thought}'}}\n\n"

    # 答案流
    async for token in agent.answer_stream():
        yield f"data: {{'type': 'content', 'content': '{token}'}}\n\n"

    yield "data: {'type': 'done'}\n\n"
```

---

## 五、推荐实施方案

### 5.1 短期（1-2天）：快速修复

1. 修复 DeepSeek R1 重复问题
2. 修复思考动画显示
3. 清理不必要的代码

### 5.2 中期（3-5天）：架构优化

1. 重构模型适配器层
2. 简化 Agent Loop
3. 添加上下文管理

### 5.3 长期（5-7天）：完整重构

参考 Claude Code 六层架构进行完整重构

---

## 六、验收标准

### 6.1 快速修复验收

- [ ] DeepSeek R1 不重复输出
- [ ] 思考动画正常显示
- [ ] 其他模型不受影响

### 6.2 架构优化验收

- [ ] 模型适配器清晰
- [ ] Agent Loop 简化
- [ ] 上下文管理正常

### 6.3 完整重构验收

- [ ] 六层架构清晰
- [ ] 真正 Tool Call
- [ ] 智能压缩
- [ ] 可扩展 Skills

---

## 七、下一步行动

1. **评审本方案**: 请审阅并选择方案
2. **确认后开始实施**: 推荐方案B（参考 Claude Code 重构）

---

**文档结束**
