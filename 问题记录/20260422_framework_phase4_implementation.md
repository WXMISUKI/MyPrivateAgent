# MyPrivateAgent 框架抽离 Phase 4 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：补齐统一事件协议的测试，并让 SSE 链路更明确地消费 `AgentEvent`

---

## 本次实施范围

本轮聚焦两件事：

1. 给 `AgentEvent / AgentRunContext / ToolSpec` 增加自动化测试
2. 在前后端 SSE 链路中增加统一事件归一化层，减少隐式字符串判断

---

## 测试补充

新增：

- `tests/agent_framework/test_events.py`

覆盖内容：

1. `AgentEventFactory` 是否正确生成事件
2. `payload` 是否能被正确扁平化到顶层
3. `AgentRunContext` 是否能记录状态和工具历史
4. `ToolSpec.to_dict()` 是否能正确序列化 `render_mode`

当前 `agent_framework` 已具备基础回归覆盖：

- provider registry
- adapter / artifact store
- event / runtime / tool metadata

---

## SSE 协议收口

### 1. 前端新增事件归一化层

新增：

- `frontend-vue/src/services/agentEvents.js`

作用：

- 统一读取 `payload`
- 兼容顶层字段和 `payload` 字段
- 统一输出：
  - `content`
  - `reasoning_content`
  - `tool_spec`
  - `render_mode`

这使前端不需要再假设所有字段都一定在顶层。

### 2. Conversation Store 改为先归一化事件

`frontend-vue/src/stores/conversation.js`

发送消息和重新生成两条流式链路，都改成先调用：

- `normalizeAgentEvent(data)`

然后再按统一结构处理。

### 3. 前端开始消费 render_mode

`frontend-vue/src/views/ChatView.vue`

新增：

- `renderMessageContent(message)`
- `renderPlainText(content)`

现在当消息带：

- `renderMode === 'plain_text'`

时，不再强制按 Markdown 渲染，避免确定性工具结果被误解释为 Markdown 样式。

### 4. 后端聊天路由兼容 payload 读取

`backend/routers/chat.py`

新增 `_extract_event_field()`，在流式保存 assistant 内容时兼容从：

- 顶层字段
- `payload`

两种位置读取 `content`

这样即使事件协议继续演进，聊天存储层也不容易被打断。

---

## 本轮收益

1. `AgentEvent` 已不再只是“结构定义”，而是有测试保护
2. 前端开始真正围绕统一事件协议消费数据
3. `plain_text` 渲染路径已接通，工具型结果更稳定
4. 后续做完整事件卡片化和 structured renderer 时，前置条件已经具备

---

## 当前限制

1. 前端仍然以 `type` 分支驱动，不是完整 reducer/event bus
2. `tool_spec` 目前只做了基本透传，尚未用于卡片渲染
3. 还没有真正的前端自动化测试
4. SSE 仍是文本流，不是更强类型化的 WebSocket 事件总线

---

## 下一阶段建议

建议第五步优先做：

1. 继续扩展前端 renderer 分级：`markdown / plain_text / structured_card`
2. 将 tool result 与 artifact result 逐步卡片化
3. 把 `AgentHarness` 的状态流转做成更显式的状态机测试
4. 开始准备 monorepo/package 化目录迁移
