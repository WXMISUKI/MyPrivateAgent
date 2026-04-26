# Phase 45 实施记录：启动自检 / 健康检查 / 最小 Smoke 第一版

## 时间

- 日期：2026-04-25
- 状态：已实施

## 本次实施目标

围绕“先保证项目正常运行、功能能用、演示稳定”这一目标，补齐启动前自检、运行态健康检查和最小 smoke 验证入口，降低演示前排障成本。

## 本次实施范围

### 1. 新增启动诊断服务

- 文件：`backend/services/startup_diagnostics_service.py`

新增 `StartupDiagnosticsService`，当前会统一检查：

- `.env` 与默认模型配置
- 数据库连接
- 关键目录是否存在
- Vue SPA 构建产物是否就绪
- 可用 server preset 列表

输出统一结构：

- `status`
- `checks`
- `summary`

这使本地启动前排障有了统一入口，而不是靠分散日志和异常堆栈。

### 2. 新增健康检查接口

- 文件：`backend/routers/health.py`
- 文件：`backend/agent_server/router_registry.py`

新增：

- `GET /api/health`

当前该接口会直接返回启动诊断报告，可用于：

- 本地快速探活
- 前后端联调前检查
- 演示前确认环境是否处于可用状态

### 3. 新增命令行 Doctor / Smoke

- 文件：`backend/scripts/doctor.py`
- 文件：`backend/scripts/smoke_check.py`

当前提供：

- `python scripts/doctor.py`
  - 输出启动诊断 JSON
  - 存在关键失败项时返回非 0 退出码

- `python scripts/smoke_check.py`
  - 基于 `TestClient` 做最小后端 smoke
  - 当前验证：
    - `/api/health`
    - `/api/models`

这样即使不启动真实服务，也能先验证后端基础组装是否正常。

### 4. README 启动指引补强

- 文件：`README.md`

新增：

- 启动前执行 `doctor.py`
- 最小 smoke 执行方式
- `/api/health` 使用说明

## 新增/更新测试

### 后端

- `tests/agent_framework/test_startup_diagnostics_service.py`
  - 验证报告聚合状态与 summary 统计

- `tests/agent_framework/test_health_router.py`
  - 验证 `/api/health` 路由返回诊断结果

## 验证结果

后端：

```powershell
python -m unittest tests.agent_framework.test_startup_diagnostics_service tests.agent_framework.test_health_router tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_permissions_router tests.agent_framework.test_run_trace_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_planner_service tests.agent_framework.test_subagent_service tests.agent_framework.test_orchestrator_service
```

- 48 条用例通过

## 当前阶段价值

这一步不是继续“加能力”，而是补运行稳定性收口：

- 项目现在有统一启动自检入口
- 有可直接探活的健康接口
- 有最小后端 smoke 脚本

这比继续深挖更复杂的多智能体或学习治理，更符合当前“先确保能稳定跑、稳定展示”的目标。

## 下一步建议

1. 给前端增加一个对应的最小“演示前检查”脚本或文档化清单
2. 再补一条轻量级的认证 + 会话创建 smoke
3. 逐步把聊天主链路的 SSE 异常兜底再收一遍
