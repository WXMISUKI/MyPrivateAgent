# Phase 50 实施记录：Demo 默认 SQLite，本地优先存储模式

## 时间

- 日期：2026-04-26
- 状态：已实施

## 本次实施目标

把项目从“默认依赖外部 MySQL”调整为“demo 默认本地可运行”，更贴近成熟 agent 工具的本地优先使用方式。

## 本次实施范围

### 1. 配置层支持存储模式切换

- 文件：`backend/config.py`

新增：

- `DB_MODE`
  - 默认值：`sqlite`
- `LOCAL_DATA_DIR`
- `SQLITE_PATH`
- `DATABASE_URL`
  - 当 `DB_MODE=sqlite` 时自动指向本地 SQLite
  - 当 `DB_MODE=mysql` 时才使用原 MySQL 连接串

### 2. 默认数据库引擎改为本地 SQLite

- 文件：`backend/database.py`

当前行为：

- 默认自动创建 `.myagent` 本地目录
- 默认使用本地 SQLite
- 保持原 SQLAlchemy 会话工厂不变

这意味着现有业务代码和 router/service 基本无需改动。

### 3. 启动初始化兼容 SQLite / MySQL

- 文件：`backend/agent_server/bootstrap.py`

当前：

- 只有 `DB_MODE=mysql` 时才执行 `CREATE DATABASE`
- `sqlite` 模式下直接初始化本地文件数据库

所以 demo 现在默认不再需要本地 MySQL 服务。

### 4. 启动自检增强

- 文件：`backend/services/startup_diagnostics_service.py`

当前会明确显示：

- 当前存储模式
- SQLite 文件路径或数据库连接地址

让 demo 使用者更容易理解当前运行方式。

### 5. 文档同步

- `README.md`
  - 明确写明 demo 默认 SQLite
  - MySQL 改成显式可选配置
- `docs/demo_storage_architecture_plan.md`
  - 说明本地优先、数据库可选的存储设计方向

## 当前阶段价值

这一步非常关键，因为它把项目的默认使用门槛明显降下来了：

- 不需要先安装和配置 MySQL
- 拉起后端即可运行 demo
- 仍然保留后续接业务数据库的路径

这比直接要求 demo 用户先接入外部数据库，更符合成熟智能体工具的本地优先思路。

## 下一步建议

1. 继续保持 SQLite 作为 demo 默认模式
2. 后续再逐步抽象成 `Storage Adapter`
3. 真正业务项目再显式切换到 MySQL/PostgreSQL
