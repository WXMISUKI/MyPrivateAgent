# Phase 47 实施记录：Chat SSE Smoke 与 Fallback Done 收口

## 时间

- 日期：2026-04-26
- 状态：已实施

## 本次实施目标

继续围绕“输出流畅、展示稳定”的目标，收口聊天 SSE 最容易造成前端卡住的问题：

- 流式响应只有 content、没有 done
- 前端拿不到 conversation_id
- 演示前无法快速确认 SSE 主链路是否正常

## 本次实施范围

### 1. Chat 路由补 Fallback Done

- 文件：`backend/routers/chat.py`

当前在流式聊天里：

- 如果运行时已经产生 `actual_content`
- 但上游没有发出显式 `done`

系统现在会自动补发：

- `type=done`
- `content=actual_content`
- `message_id`（如已保存）

这可以显著降低前端停留在“生成中”的风险。

### 2. 新增聊天 SSE Smoke 脚本

- 文件：`backend/scripts/chat_stream_smoke.py`

当前脚本使用 stub orchestrator，不依赖真实模型调用，验证：

- `POST /api/auth/guest`
- `POST /api/chat`
- SSE 中是否包含：
  - `conversation_id`
  - 流式 `content`
  - `done`

这比纯健康检查更接近真正的聊天展示链路。

### 3. 新增自动化回归

- 文件：`tests/agent_framework/test_chat_stream_smoke.py`

当前测试使用临时 SQLite 和 stub orchestrator，验证：

- SSE 首先返回 `conversation_id`
- 流式内容能正常输出
- 即使没有显式 done，上层也会补出 fallback `done`
- fallback `done` 的内容会是完整累计结果

### 4. README 启动说明补充

- 文件：`README.md`

新增 `chat_stream_smoke.py` 用法，作为当前演示前最接近真实聊天体验的一条 smoke。

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_chat_stream_smoke tests.agent_framework.test_auth_conversation_smoke tests.agent_framework.test_startup_diagnostics_service tests.agent_framework.test_health_router tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_permissions_router tests.agent_framework.test_run_trace_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_planner_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 50 条用例通过

## 当前阶段价值

这一步很实际：

- 聊天 SSE 现在多了一层结束态兜底
- 演示前已经有一条不依赖真实模型的流式主链路 smoke
- “前端一直转圈”这一类问题的风险进一步下降

## 下一步建议

1. 再补一条聊天错误事件 / 空响应的 smoke
2. 再检查前端 `停止生成` 与 `错误提示` 的状态收口
3. 暂时不要继续深挖更复杂的框架能力，先把展示稳定性彻底收平
