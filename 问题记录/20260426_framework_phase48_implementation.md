# Phase 48 实施记录：Chat Empty Response / Error 收口

## 时间

- 日期：2026-04-26
- 状态：已实施

## 本次实施目标

继续围绕“输出流畅、避免前端卡住”的目标，收口聊天主链路里两个最常见的展示问题：

- 上游空响应
- SSE 中途返回 `error` 事件

## 本次实施范围

### 1. 后端空响应兜底

- 文件：`backend/routers/chat.py`

当前当聊天流结束后：

- 如果没有 `actual_content`
- 也没有显式 `done`

系统现在会主动返回：

- 一条 `content`
  - `本次未生成有效回复，请重试`
- 一条 `done`
  - 同样带回兜底文案

这样可以避免前端出现空白 assistant 消息或一直等待结束态。

### 2. 前端错误事件收尾

- 文件：`frontend-vue/src/stores/conversation.js`

当前流式聊天和重新生成两条链路都已支持：

- `event.type === 'error'`

收到后会立即：

- 结束生成状态
- 用错误文案收尾 assistant 消息
- resolve 当前请求

这样可以减少“后端已报错但前端仍停留在生成中”的问题。

### 3. 新增空响应 Smoke 与自动化回归

- 文件：`backend/scripts/chat_empty_response_smoke.py`
- 文件：`tests/agent_framework/test_chat_empty_response_smoke.py`

当前验证：

- 上游完全空响应时
- `/api/chat` 仍会返回可展示的 fallback content
- 且最终有 `done`

### 4. 前端 store 回归补强

- 文件：`frontend-vue/src/stores/__tests__/conversation.test.js`

新增覆盖：

- 流式返回 `error` 事件时 assistant 消息会正常收尾
- 成功但空响应时 assistant 消息不会卡在生成中

### 5. README 启动说明补充

- 文件：`README.md`

新增 `chat_empty_response_smoke.py` 用法说明。

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_chat_stream_smoke tests.agent_framework.test_chat_empty_response_smoke tests.agent_framework.test_auth_conversation_smoke tests.agent_framework.test_startup_diagnostics_service tests.agent_framework.test_health_router tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_permissions_router tests.agent_framework.test_run_trace_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_planner_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 51 条用例通过

前端：

- 本轮补了 `conversation store` 相关测试用例，建议下一轮一起跑 `npm test`

## 当前阶段价值

到这一步，演示前的最小稳定性检查已经更完整：

- 启动自检
- 基础 API smoke
- 认证 / 会话 smoke
- 聊天 SSE 主链路 smoke
- 聊天空响应兜底 smoke

这已经明显更接近“项目能正常跑、功能能展示、前端不容易卡死”的目标。

## 下一步建议

1. 跑一遍前端 `npm test` 和 `npm run build`，确认本轮前端 store 改动无回归
2. 再补一条聊天 `error` 事件的后端脚本化 smoke
3. 再系统收一遍前端“停止生成”按钮链路
