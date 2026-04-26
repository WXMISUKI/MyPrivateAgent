# Phase 32 实施记录：反馈入口前端闭环与反馈分析接口

## 本次目标
- 补齐前端消息级反馈入口（点赞/点踩/原因选择）。
- 在后端提供可运营的 feedback analytics 聚合能力。
- 打通 `selected_reasons` 数据链路，支持后续治理与回滚决策。

## 主要改动

### 1. 后端反馈模型增强
- 文件：`backend/schemas.py`
- 新增请求字段：
  - `ConversationFeedbackCreate.selected_reasons: Optional[List[str]]`
- 新增分析响应模型：
  - `FeedbackDimensionStat`
  - `FeedbackRollbackCandidate`
  - `ConversationFeedbackAnalyticsResponse`

### 2. 会话服务新增反馈分析能力
- 文件：`backend/services/conversation_service.py`
- `create_feedback()` 支持 `selected_reasons` 并写入 `feedback_metadata.selected_reasons`。
- 新增 `get_feedback_analytics()`：
  - 按 `scope / prompt_key / practice_id` 聚合总反馈与负反馈率
  - 输出 `rollback_candidates`（默认样本数 >= 2 且负反馈率 >= 0.6）

### 3. 暴露反馈分析 API
- 文件：`backend/routers/conversations.py`
- 新增接口：
  - `GET /api/conversations/analytics/feedback`
- 既有接口增强：
  - `POST /api/conversations/{conversation_id}/feedback` 支持 `selected_reasons`

### 4. 前端消息级反馈闭环
- 文件：`frontend-vue/src/views/ChatView.vue`
  - 助手消息新增点赞/点踩按钮
  - 点踩可多选原因并补充文本说明
  - 提交态、错误态、已提交态（含 scope / learning id / 原因）可见
- 文件：`frontend-vue/src/stores/conversation.js`
  - `submitMessageFeedback()` 支持 `selectedReasons`
  - 消息反馈状态保留 `metadata`

### 5. 回归测试补充
- 文件：`tests/agent_framework/test_conversation_service.py`
- 新增覆盖：
  - `selected_reasons` 持久化
  - feedback analytics 聚合与回滚候选判断

## 结果
- 前端“消息反馈 -> 后端记录 -> 负反馈学习”闭环从 API 层提升到可用交互层。
- 系统具备基础反馈治理能力，可按 prompt/practice 识别高风险条目。
- 为后续 Workbench 管理页和自动回滚策略提供稳定统计接口。

## 后续建议
- 增加 feedback analytics 专用前端页面（趋势图、过滤器、回滚操作）。
- 在反馈提交中支持消息级唯一约束或幂等更新，避免重复记录干扰分析。
- 补 `/api/chat` 到 feedback 的端到端自动化链路测试。
