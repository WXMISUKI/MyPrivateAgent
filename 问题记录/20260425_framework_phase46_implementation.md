# Phase 46 实施记录：Auth / Conversation Smoke 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

继续围绕“先保证正常运行、功能能用”的目标，补一条比健康检查更接近真实使用的最小主链路 smoke：

- 游客登录
- 获取当前用户
- 创建会话
- 拉取会话列表与详情

## 本次实施范围

### 1. 新增认证 / 会话 smoke 脚本

- 文件：`backend/scripts/auth_session_smoke.py`

当前脚本基于 `TestClient` 直接验证：

- `POST /api/auth/guest`
- `GET /api/auth/me`
- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{id}`

这条检查比纯健康接口更接近真实 demo 主链路，但仍然不触发真实模型调用。

### 2. 新增自动化回归

- 文件：`tests/agent_framework/test_auth_conversation_smoke.py`

测试使用临时 SQLite 数据库，不依赖本地 MySQL 环境，验证：

- 游客登录成功
- Bearer Token 可正常鉴权
- 会话创建成功
- 会话列表与详情查询成功

这使“认证 + 会话”这条最小基础链路进入自动化守门。

### 3. README 启动说明补充

- 文件：`README.md`

新增 `auth_session_smoke.py` 的执行说明，便于演示前快速检查主链路。

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_auth_conversation_smoke tests.agent_framework.test_startup_diagnostics_service tests.agent_framework.test_health_router tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_permissions_router tests.agent_framework.test_run_trace_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_planner_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 49 条用例通过

## 当前阶段价值

现在项目用于“可运行 / 可展示”的基础检查已经形成三层：

- `doctor.py`
  - 看环境与依赖是否就绪
- `smoke_check.py`
  - 看后端基础探活是否正常
- `auth_session_smoke.py`
  - 看认证与会话主链路是否正常

这已经明显比单纯靠手工点页面更稳。

## 下一步建议

1. 再补一条不依赖真实模型的聊天 SSE 结束态 smoke
2. 收一遍前端“生成中 / 失败 / 停止”状态切换
3. 再考虑更深的运行时治理完善
