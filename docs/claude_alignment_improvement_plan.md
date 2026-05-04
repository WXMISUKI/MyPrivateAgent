# 通用智能体框架下一阶段完善方案

本文档记录 `MyPrivateAgent` 作为通用智能体框架，继续向 Claude Code 类成熟智能体靠拢时的下一阶段方案。目标不是继续堆单点功能，而是把现有能力收口成一套可治理、可评测、可复用的运行时底座。

## 结论

当前项目已经具备以下基础：

- `AgentHarness + Orchestrator + ChatService` 主链路
- planner / todo 域
- pseudo-subagent 到 scheduler 的过渡层
- hooks / permissions / doctor / quality gate
- MCP registry / runtime / session 骨架
- skill runtime、learning governance、run trace、runtime surface

下一阶段最重要的不是再加 UI，而是补齐三件事：

1. 统一运行时协议和状态机
2. 把 scheduler / subagent / hook / MCP 收口到同一套治理内核
3. 把 Claude 风格的记忆、settings、subagents、slash commands 变成框架级能力面

## Claude 公开机制对照

根据 Claude Code 的公开文档，成熟框架通常具备这些结构：

- 分层记忆：`CLAUDE.md`、项目记忆、用户记忆、企业策略
- 子智能体：`.claude/agents/` 下的角色化 subagents
- hooks：`PreToolUse`、`PostToolUse`、`SessionStart`、`Stop` 等事件
- slash commands：`/doctor`、`/model`、`/permissions`、`/memory`、`/agents`、`/mcp`
- MCP：作为外部能力发现和调用的标准协议

对应到本项目，说明我们不缺“功能点”，缺的是“统一组织方式”。

## 当前差距

### 已有，但还没收口

- planner 具备了执行状态，但还不是真正的调度中枢
- subagent 已有注册和角色信息，但还没完全变成第一类运行时对象
- hooks 已接入主链路，但治理边界仍需统一到事件协议
- quality gate 已可一键执行，但还需要与运行时 trace / CI artifact 更深绑定

### 仍需补齐

- 统一 `AgentRun` / `AgentEvent` / `RunTrace` 协议
- 明确状态机：`INIT / PLANNING / ACTING / WAITING_PERMISSION / OBSERVING / FINALIZING / DONE / FAILED / ABORTED`
- 真正的 fan-out / collect / merge 调度层
- 命令层：把常用治理动作固化为 `/doctor`、`/plan`、`/gaps`、`/permissions`、`/mcp`、`/model`
- 分层记忆：把 `GLOBAL_AGENT.md`、`PROJECT_AGENT.md`、local 覆写、运行时能力面合并成一致入口
- 系统性评测：benchmark、回归基线、失败分类、报告产物

## 下一阶段方案

### P0: 统一运行时内核

目标：让所有执行路径共用同一套状态、事件、trace 和停止原因。

工作项：

1. 定义统一事件协议
2. 定义统一运行状态机
3. 统一 planner / tool / hook / subagent / MCP 的 trace 入口
4. 让 doctor 和 capability gate 直接消费统一 trace

验收标准：

- 任意一次执行都能回放
- 任意一次失败都能定位到状态和事件
- planner、hook、subagent、MCP 不再是散点日志

### P1: 真正的调度器

目标：把“计划项”升级成“父子执行模型”，而不是聊天链路里的临时分支。

工作项：

1. planner item -> child run 映射
2. fan-out / collect / merge
3. child run 状态：`queued / running / completed / failed / cancelled`
4. 统一 child run 审计和 merge summary
5. 让 scheduler policy 决定是否允许 spawn、fallback、retry

验收标准：

- 一个 plan item 可以稳定生成多个 child run
- 失败不会静默消失
- merge 结果和原始 child 结果都可追踪

### P2: Claude 风格的配置与命令层

目标：把高频操作变成可发现、可复用、可组合的命令和配置。

工作项：

1. 分层记忆
   - `GLOBAL_AGENT.md`
   - `PROJECT_AGENT.md`
   - `PROJECT_AGENT.local.md`
   - 企业策略位预留
2. 子智能体正式注册
   - `name`
   - `description`
   - `tools`
   - `preferred_models`
   - `trigger_conditions`
3. slash command 层
   - `/doctor`
   - `/plan`
   - `/gaps`
   - `/permissions`
   - `/mcp`
   - `/model`
4. settings / policy 分层
   - 项目级
   - 用户级
   - 本地覆写级

验收标准：

- 框架能力不再依赖“记住某条操作”
- 配置、权限、角色、命令都可发现
- 子智能体选择和工具白名单可解释

### P3: 评测、治理与回归

目标：让框架演进可控，而不是靠人工感觉判断。

工作项：

1. 固定 benchmark cases
2. 回归健康度门禁
3. provider / model 质量指标
4. failure taxonomy
5. artifact 输出和 CI summary

建议指标：

- 首 token 时间
- completion timeout
- fallback 触发率
- tool failure rate
- 回归健康度分数

验收标准：

- 每次改动都能自动判断是否回归
- CI 能输出可读摘要和机器可消费产物
- 失败可直接映射到修复建议

### P4: 前端治理台

目标：把内部治理变成可见的工作台，而不是只能读日志。

工作项：

1. scheduler timeline
2. subagent 运行视图
3. hook / permission 视图
4. MCP 健康和调用历史
5. learning / capability gap 运营视图

## 推荐实施顺序

1. P0 统一运行时内核
2. P1 真正的调度器
3. P2 Claude 风格配置与命令层
4. P3 评测、治理与回归
5. P4 前端治理台

## 本阶段建议先做的 3 件事

1. 先把统一事件协议和状态机定下来
2. 再把 scheduler 做成第一类服务
3. 最后补齐 memory / command / settings 的框架层入口

## 参考资料

- Claude Code memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Claude Code subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Claude Code hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code slash commands: https://docs.anthropic.com/en/docs/claude-code/slash-commands
