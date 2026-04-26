# Phase 31 实施记录：用户反馈关联 Runtime Effect 闭环

## 本次目标
- 把用户对助手回复的反馈正式纳入框架主链。
- 将反馈与 `runtime_knowledge_effect` artifact 关联起来，支持后续评估。
- 对负反馈自动生成 `Learning(source=user_feedback)`，让自学习系统形成最小闭环。

## 主要改动

### 1. 新增反馈持久化模型
- 文件：`backend/models.py`
- 新增 `MessageFeedbackRecord`
- 关键字段：
  - `conversation_id`
  - `message_id`
  - `feedback_type`
  - `score`
  - `comment`
  - `runtime_artifact_id`
  - `runtime_scope`
  - `selected_items`
  - `stop_reason`
  - `created_learning_id`

### 2. 补充反馈 Schema
- 文件：`backend/schemas.py`
- 新增：
  - `ConversationFeedbackCreate`
  - `ConversationFeedbackResponse`

### 3. 在会话服务中实现反馈闭环
- 文件：`backend/services/conversation_service.py`
- 新增能力：
  - 自动定位当前会话最近一条 assistant 消息
  - 自动读取最近一条 `runtime_knowledge_effect`
  - 创建反馈记录
  - 对 `negative` 反馈自动创建 `Learning`

### 4. 开放反馈 API
- 文件：`backend/routers/conversations.py`
- 新增接口：
  - `POST /api/conversations/{conversation_id}/feedback`
  - `GET /api/conversations/{conversation_id}/feedback`

### 5. 文档与测试
- 文件：`tests/agent_framework/test_conversation_service.py`
- 新增覆盖：
  - 反馈关联 runtime effect
  - 负反馈生成 learning
  - 反馈列表查询
- 文件：`docs/agent_framework_starter_guide.md`
- 补充 feedback layer 的 starter 约束

## 结果
- 自学习系统不再只依赖对话后分析。
- 运行期知识命中开始具备“用户反馈 -> effect -> learning”的最小评估闭环。
- 这一步让框架更接近成熟 harness 的可评估、自改进路径。

## 后续建议
- 增加反馈聚合视图，统计不同 practice/prompt 的负反馈率。
- 支持将反馈直接标记到具体 `prompt_key` / `practice_id`。
- 为 feedback 加入前端入口和调试面板联动。
