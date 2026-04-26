# Phase 33 实施记录：消息级反馈精确绑定与反馈分析工作台

## 本次目标
- 解决反馈记录与助手消息“弱关联”问题，确保反馈精确绑定到具体 assistant message。
- 将反馈分析接口落地为前端可用页面，形成基础治理工作台入口。

## 主要改动

### 1. chat 流式 done 事件注入 message_id
- 文件：`backend/routers/chat.py`
- 做法：
  - 在流式转发过程中暂存 `done` 事件
  - 先保存 assistant 消息，再将数据库 `message_id` 注入 `done` 事件并发送
- 结果：
  - 前端可在本轮回复结束时拿到真实 message_id
  - 后续反馈不再依赖“最近一条 assistant 消息”的模糊匹配

### 2. assistant 持久化返回值增强
- 文件：`backend/services/chat_service.py`
- `save_assistant_message()` 改为返回保存后的消息对象（含 `id`），供流式路由注入使用。

### 3. 前端流式事件与消息 ID 对齐
- 文件：`frontend-vue/src/services/agentEvents.js`
  - 标准化事件新增 `message_id`
- 文件：`frontend-vue/src/stores/conversation.js`
  - 在 `done` 事件阶段把本地 assistant 消息 `id` 更新为服务端 message_id

### 4. 反馈分析工作台页面
- 文件：`frontend-vue/src/views/FeedbackAnalyticsView.vue`
- 新增能力：
  - 调用 `/api/conversations/analytics/feedback`
  - 支持窗口天数与候选最小样本筛选
  - 展示总览指标、scope/prompt/practice 维度统计、回滚候选表

### 5. 前端入口打通
- 文件：`frontend-vue/src/router/index.js`
  - 新增路由 `/feedback-analytics`
- 文件：`frontend-vue/src/components/AppSidebar.vue`
  - 新增“反馈分析”菜单
- 文件：`frontend-vue/src/App.vue`
  - 新增导航处理逻辑
- 文件：`frontend-vue/src/services/commands.js`
  - 新增 `/feedback` 命令
- 文件：`frontend-vue/src/views/ChatView.vue`
  - 命令执行与帮助信息接入反馈分析页

## 验证结果
- 后端关键单测通过：
  - `tests.agent_framework.test_chat_service`
  - `tests.agent_framework.test_conversation_service`
  - `tests.agent_framework.test_orchestrator_service`
- 前端 `npm run build` 通过。

## 后续建议
- 为“每条 assistant 消息每个用户仅允许一条反馈”增加幂等约束（DB 唯一键或 upsert）。
- 在反馈分析页增加“按 key 一键跳转到治理页/回滚动作”的操作链路。
- 增加 chat SSE 到 feedback 的端到端自动化测试，覆盖 message_id 注入行为。
