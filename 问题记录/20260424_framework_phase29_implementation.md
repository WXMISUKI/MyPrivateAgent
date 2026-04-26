# Framework Phase 29 实施记录

## 日期
2026-04-24

## 主题
前端调试视图：Runtime Knowledge / Tool Execution 可视化

## 背景
Phase 24 和 Phase 28 已经让 runtime 侧具备了：

- tool execution trace
- cache hit
- runtime knowledge 选中与跳过信息
- knowledge effect artifact

但这些信息此前主要存在于：
- 后端事件
- artifact
- 日志

前端仍然只能看到最终消息和工具结果，不像成熟 harness/workbench 那样可直接观察运行时决策。

## 本次目标

把 runtime trace 从“后端可见”推进到“前端可见”：

1. 后端显式发出 runtime knowledge 状态事件
2. 前端消费并保存运行调试元数据
3. 聊天界面显示：
   - runtime knowledge 选中/跳过信息
   - tool execution 来源、耗时、缓存命中

## 本次改动

### 1. Orchestrator 发出 runtime knowledge 状态事件
- 文件：`backend/orchestrator.py`

在 runtime knowledge 注入成功后，新增一条流式事件：

- `type = "status"`
- `status_kind = "runtime_knowledge"`

携带：
- `scope`
- `prompt_count`
- `practice_count`
- `selected_items`
- `skipped_items`

这使前端不再需要猜测本次到底注入了哪些知识。

### 2. 事件归一化增强
- 文件：`frontend-vue/src/services/agentEvents.js`

新增归一化字段：
- `status_kind`
- `tool_execution`
- `cache_hit`
- `duration_ms`
- `result_source`
- `status`
- `selected_items`
- `skipped_items`
- `scope`
- `prompt_count`
- `practice_count`

### 3. Conversation Store 保存调试元数据
- 文件：`frontend-vue/src/stores/conversation.js`

新增：
- `applyAssistantDebugMetadata()`
- `upsertToolCall()`

效果：

#### assistant message
- 保存 `runtimeKnowledge`
- 保存 `toolExecution`

#### tool call
- 保存 `execution`
  - `cache_hit`
  - `duration_ms`
  - `result_source`
  - `status`

并且这些逻辑同时覆盖：
- `sendMessage()`
- `regenerateMessage()`

### 4. 新增调试面板组件
- 文件：`frontend-vue/src/components/AgentRuntimeDebugPanel.vue`

展示内容：
- Runtime Knowledge
  - `scope`
  - prompt/practice 数量
  - selected items
  - skipped items
- Tool Execution
  - source
  - cache hit/miss
  - duration
  - status

### 5. ChatView 集成
- 文件：`frontend-vue/src/views/ChatView.vue`

新增：
- assistant 消息下方渲染 `AgentRuntimeDebugPanel`
- tool call 卡片里显示执行元数据：
  - source
  - cache
  - duration

## 验证结果
- 后端定向测试通过
- 完整后端测试：61 项通过
- `frontend-vue` 生产构建通过

## 结果
这一步之后，这套框架开始更像一个真正的 agent workbench：

- 不只是“能跑”
- 也不只是“后端有日志”
- 而是前端已经能直接看到关键运行时决策

这对于后续做：
- 调试
- 评估
- demo 展示
- 框架复用

都非常重要。

## 下一步建议

优先继续做两件事：

1. **Starter / Demo Productization**
   - 增加 `weather_demo` / `knowledge_demo` 示例
   - 补“如何创建新垂域 agent”的模板或脚手架说明

2. **运行效果评估继续增强**
   - 把 runtime knowledge effect 和用户反馈关联起来
   - 为后续自动晋升/自动回滚提供依据
