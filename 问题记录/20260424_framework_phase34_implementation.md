# Phase 34 实施记录：反馈幂等约束与前端更新提交流程

## 本次目标
- 将消息反馈从“可新增”升级为“可幂等更新”。
- 保证同一用户对同一条助手消息只保留一条反馈记录，避免 analytics 被重复提交污染。

## 主要改动

### 1. 数据模型增加唯一约束
- 文件：`backend/models.py`
- 在 `MessageFeedbackRecord` 增加唯一约束：
  - `(conversation_id, message_id, user_id)` 唯一

### 2. 启动阶段补齐历史库约束初始化
- 文件：`backend/agent_server/bootstrap.py`
- 新增 `_ensure_feedback_uniqueness_constraint()`：
  - 检查 `message_feedback` 是否已存在唯一约束
  - 若不存在则尝试创建
  - 若检测到重复数据则记录告警并跳过，避免启动失败

### 3. 反馈接口改为 upsert 语义
- 文件：`backend/services/conversation_service.py`
- `create_feedback()` 新逻辑：
  - 必须先定位到 assistant message（找不到直接抛 `ValueError`）
  - 按 `(conversation_id, message_id, user_id)` 查询既有记录
  - 存在则更新，不存在则创建
  - 负反馈仅在尚未创建 learning 时生成一次 learning

### 4. API 错误语义增强
- 文件：`backend/routers/conversations.py`
- 对 `create_feedback()` 的 `ValueError` 返回 `400`，给前端明确提示（非 500）。

### 5. 前端提交策略改为“可更新”
- 文件：`frontend-vue/src/views/ChatView.vue`
- 调整：
  - 点赞/点踩与提交按钮不再因已反馈而禁用
  - 点踩面板支持回填已有负反馈原因与说明
  - 允许在同一消息上重复提交，后端统一走 upsert

### 6. 测试补充
- 文件：`tests/agent_framework/test_conversation_service.py`
- 新增覆盖：
  - 同消息重复提交走更新（不新增记录）
  - 无 assistant 消息时抛 `ValueError`

## 验证结果
- `python -m unittest tests.agent_framework.test_conversation_service tests.agent_framework.test_chat_service tests.agent_framework.test_orchestrator_service` 通过。
- `frontend-vue` 执行 `npm run build` 通过。

## 后续建议
- 为 `message_feedback` 增加独立管理接口（按 message_id 查询/删除）便于运营修复。
- 把“重复反馈更新时间”纳入统计维度，识别反复修改的高争议回复。
