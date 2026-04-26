# MyPrivateAgent 框架建设简史（精简版）

## 目标

这份文档用于替代大量分散的 `framework_phase*_implementation.md` 阶段记录，保留对当前项目仍有价值的历史主线，减少维护噪音。

如果后续只想快速理解项目是怎么演进到当前状态的，优先看这份文档，再看：

- `20260424_framework_current_status_summary.md`
- `20260425_planner_todo_progress_log.md`
- `docs/demo_runbook.md`
- `docs/test_manual.md`

## 演进主线

### 阶段 1：框架抽离与执行主链收口

时间范围：

- 2026-04-22 ~ 2026-04-23

主要结果：

- 从单项目私有助手逐步收口为通用 Agent Framework Demo
- 形成 `backend/agent_framework` 运行时层
- 形成 `backend/agent_server` 装配层
- 聊天链路逐步统一到 `AgentHarness + Orchestrator + ChatService`
- 路由层、服务层、server adapter 边界开始清晰

### 阶段 2：Preset、Auth、Runtime 治理增强

时间范围：

- 2026-04-24

主要结果：

- `create_app()` 支持 preset 与配置化装配
- 认证、工具缓存、runtime prompt / best practice 注入持续增强
- feedback 闭环开始进入主链路
- structured card、tool trace、runtime knowledge 展示逐步打通

### 阶段 3：反馈闭环与治理

时间范围：

- 2026-04-24

主要结果：

- 消息级反馈入口打通
- feedback -> runtime effect -> learning 最小闭环打通
- 反馈幂等约束补齐
- feedback analytics 基础能力引入

### 阶段 4：Planner / Scheduler / 多智能体雏形

时间范围：

- 2026-04-25

主要结果：

- 新增 Planner / Todo 领域模型
- 右侧 Planner 面板集成到聊天页
- 计划项状态可与聊天执行联动
- 伪 handoff -> spawned subagent runtime -> scheduler fan-out/fan-in
- 补齐 timeout / retry / cancellation / audit trail / planner timeline
- run trace 开始统一

### 阶段 5：MCP 与 Skill Runtime

时间范围：

- 2026-04-25

主要结果：

- MCP registry / catalog / probe / handshake / tools/call 骨架建立
- MCP capability runtime binding 建立
- MCP 前端管理面板建立
- Skill 从管理层进入 runtime selection / injection
- Skill priority / activation / conflict policy 第一版建立

### 阶段 6：运行稳定性收口

时间范围：

- 2026-04-25 ~ 2026-04-26

主要结果：

- 启动自检、健康检查、最小 smoke 完成
- auth / conversation smoke 完成
- chat SSE smoke / fallback done 完成
- 空响应兜底 / error 收尾完成
- Demo 默认存储改为本地优先 SQLite
- Demo 运行与演示手册完成
- 停止生成链路完成收口
- 统一测试手册完成

## 当前应保留的核心理解

如果只看今天仍然重要的结论，可以浓缩成下面几条：

1. 当前项目已经不是聊天 demo，而是可复用的通用智能体 demo/starter。
2. 主链路已经收口到统一执行架构，不再是多套分叉执行器。
3. Planner、Scheduler、MCP、Skill Runtime、Run Trace 都已有第一版能力。
4. 当前最重要的是保持默认可运行、默认可测试，而不是继续堆叠表面功能。

## 已删除的历史阶段文档说明

原先大量 `framework_phase*_implementation.md` 文档主要承担“每日增量记录”职责。  
这些文档在当前阶段已经带来两个问题：

- 文件数量过多，不利于快速理解项目
- 大量信息已被总进度日志、当前状态总结和运行/测试手册覆盖

因此已将历史增量信息折叠为本精简版，后续优先维护：

- 当前状态总结
- 总进度日志
- 运行手册
- 测试手册
- 必要的长期架构设计文档
