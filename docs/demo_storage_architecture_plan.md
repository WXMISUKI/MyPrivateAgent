# Demo 存储架构方案

## 目标

让智能体框架 Demo 在默认情况下无需外部数据库基础设施即可运行，同时保留外部数据库作为可选部署模式。

## 推荐默认方案

对于 Demo 和本地开发场景：

- 运行时状态放在内存中
- 持久化使用本地 SQLite
- 配置和指令存放在本地文件
- 只有真实业务需要多用户或基础设施级持久化时，才引入外部 MySQL / PostgreSQL

## 为什么这更符合成熟 Agent 的形态

公开可见的成熟 Agent 工具通常会优先使用本地 / 项目级配置与状态，而不是默认依赖外部数据库：

- Claude Code：
  - 本地 / 用户 / 项目级 settings 文件
  - `CLAUDE.md`
  - 项目本地 agent 定义
- OpenAI Codex CLI：
  - 本地配置
  - 本地状态数据库
- Gemini CLI：
  - 本地 settings 文件

常见模式不是“全部放内存”，也不是“默认接外部数据库”，而是：

1. 内存中的运行时状态
2. 本地可持久化存储
3. 可选的外部持久化能力

## 当前项目方向

### Phase S1：默认 SQLite

已实现：

- `backend/config.py`
  - 引入 `DB_MODE`
  - 默认值为 `sqlite`
  - 自动构建 `DATABASE_URL`
- `backend/database.py`
  - 本地默认使用 SQLite
  - 自动创建本地数据目录
- `backend/agent_server/bootstrap.py`
  - 仅在 `DB_MODE=mysql` 时执行 MySQL 建库流程
  - 否则直接初始化本地 SQLite 存储
- `backend/services/startup_diagnostics_service.py`
  - 对外暴露当前存储模式和真实连接目标

## 推荐下一步

1. 继续将 SQLite 保持为默认 Demo 存储方案。
2. 逐步通过 service / repository interface 抽离存储适配层。
3. 仅在确实能显著降低复杂度时，才把部分 Demo 友好的状态从 SQL 表迁移到可选的文件存储。
4. 对真实部署场景保留 MySQL 作为显式 opt-in 模式，而不是默认路径。
