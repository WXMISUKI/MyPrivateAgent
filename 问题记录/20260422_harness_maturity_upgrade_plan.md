# MyPrivateAgent Harness 成熟度升级方案

## 文档信息
- 创建日期: 2026-04-22
- 版本: v1.0
- 状态: 待评审
- 目标: 对齐成熟智能体框架的最佳实践，系统性提升稳定性、可维护性、可扩展性

---

## 一、现状判断

当前项目已经具备一个“可运行的 Agent 原型框架”，核心能力包括：

- 基础 Agent Loop
- 流式输出
- Tool Registry
- 简单权限机制
- 上下文窗口
- 会话状态管理
- 前端工具调用展示

但从最佳实践看，当前仍处于“原型工程化阶段”，距离 Claude Code、Codex CLI、Cursor Agent 等成熟智能体框架还有明显差距。

### 当前阶段定位

建议将当前系统定位为：

**L2: 可运行的 Agent 原型**

而成熟框架通常至少达到：

**L4: 生产可维护的 Agent 平台**

---

## 二、与成熟框架的核心差距

### 2.1 Agent Loop 仍偏流程脚本，不是显式状态机

当前 `AgentHarness` 已经能处理：

- 模型流式响应
- 工具调用
- 工具结果回填
- 基础错误处理

但仍缺少成熟框架常见的显式状态建模：

- `planning`
- `acting`
- `awaiting_tool_result`
- `awaiting_permission`
- `observing`
- `finalizing`
- `aborted`
- `failed`

结果是：

- 执行流不够可追踪
- 恢复与中断能力弱
- 多工具、多轮任务容易出现隐式分支膨胀

### 2.2 工具系统还不是平台化能力

当前工具调用已经走通，但工具平台仍缺少统一治理：

- 工具是否确定性无显式元数据
- 工具输出格式没有统一渲染契约
- 工具缓存、幂等、超时、重试策略未标准化
- Tool schema、executor、formatter 没有一一对应关系

这次天气问题就是典型案例：

- schema 正确
- tool_call 解析正确
- 但 executor、formatter、final answer 策略没有统一治理

### 2.3 上下文与记忆还停留在基础压缩层

`ContextManager` 与 `MemoryManager` 当前更接近：

- 短期消息压缩器
- 会话状态记录器

但成熟框架通常会显式区分：

1. 短期对话上下文
2. 执行 scratchpad
3. 工具输出 artifact
4. 长期记忆
5. 用户偏好 / 项目偏好

当前缺失 artifact 层，导致长工具输出容易直接污染主上下文。

### 2.4 权限系统还缺少可恢复性和持久化

`PermissionService` 目前主要是内存态请求管理，适合作为原型，但距离成熟框架还差：

- 权限请求持久化
- 会话恢复
- 用户审批日志
- 规则级授权缓存
- 危险命令分级策略

### 2.5 可观测性不足

当前日志很多，但更偏 debug print，不够结构化。成熟框架至少会具备：

- `run_id`
- `conversation_id`
- `iteration`
- `tool_call_id`
- `stop_reason`
- `latency_ms`
- `retry_count`

没有这些结构化 trace，问题复盘成本会很高。

### 2.6 测试体系远不够

当前项目对真实高风险链路的回归覆盖仍然不足，尤其缺少：

- 流式 tool_call 组装测试
- assistant/tool 回填协议测试
- 确定性工具直出测试
- 前端 SSE 消费测试
- ORM 生命周期边界测试

### 2.7 前端渲染策略不够分级

当前 assistant 文本统一走 Markdown 渲染。这对开放式聊天是合适的，但对以下内容不够稳：

- 工具结果
- 表格化结果
- 检索摘要
- 天气、时间、数值型输出

成熟框架通常不会用一个 renderer 处理所有消息。

---

## 三、升级目标

本轮升级建议达成以下目标：

1. Agent Loop 状态显式化
2. Tool 平台能力统一化
3. 确定性结果渲染策略平台化
4. 上下文、artifact、记忆分层
5. 可观测性与回归测试补齐

---

## 四、升级原则

### 4.1 单一事实来源

每个工具必须明确只有一套：

- schema
- executor
- formatter
- render_mode

### 4.2 确定性优先

天气、时间、检索摘要、数据库查询等结果，默认不再交给模型自由重写。

### 4.3 事件先于字符串

前后端交互应尽量基于结构化事件，而不是依赖字符串内容猜测状态。

### 4.4 状态机先于分散 if/else

执行流必须有明确状态、停止原因和恢复点。

### 4.5 artifact 先于直接塞上下文

长内容、网页内容、工具原始输出不直接进主 prompt，只进 artifact。

### 4.6 trace 先于调试打印

日志要支持问题复盘，而不是仅供临时调试。

---

## 五、分阶段实施方案

## 阶段 1：稳定性内核升级

### 目标

让当前框架从“能跑”提升到“稳定、可复盘”。

### 关键任务

1. 统一 `AgentEvent` 事件协议
2. 给工具增加元数据字段
3. 确定性工具结果直出机制平台化
4. 修复 ORM 生命周期和流尾逻辑边界
5. 增加最小回归测试集

### 建议新增的数据结构

```python
class AgentEvent(TypedDict):
    type: str
    run_id: str
    conversation_id: int | None
    iteration: int | None
    payload: dict
```

### Tool 元数据建议

```python
{
  "name": "search",
  "deterministic": True,
  "render_mode": "plain_text",
  "safe_to_rephrase": False,
  "supports_cache": True,
  "timeout_seconds": 10
}
```

### 验收标准

- [ ] 所有流式消息都有统一事件结构
- [ ] 确定性工具可直接返回
- [ ] 工具调用错误不再进入死循环
- [ ] 至少覆盖 5 个核心回归测试

---

## 阶段 2：AgentHarness 状态机化

### 目标

将当前 Harness 重构为可恢复、可追踪、可扩展的执行状态机。

### 建议状态

- `INIT`
- `GENERATING`
- `TOOL_CALLING`
- `WAITING_PERMISSION`
- `OBSERVING`
- `FINALIZING`
- `DONE`
- `FAILED`
- `ABORTED`

### 建议新增运行上下文

```python
class AgentRunContext:
    run_id: str
    conversation_id: int | None
    user_id: int | None
    iteration: int
    max_iterations: int
    tool_history: list
    stop_reason: str | None
    metadata: dict
```

### 要解决的问题

- 重复工具调用抑制
- 同参数工具缓存
- 工具失败熔断
- 中断与恢复
- stop_reason 统一输出

### 验收标准

- [ ] 每次执行都有 run_id 和 stop_reason
- [ ] 失败路径可清晰定位到状态阶段
- [ ] 同一错误不会无限重复调用工具

---

## 阶段 3：上下文、Artifact、记忆分层

### 目标

让长对话、长工具结果、复杂任务不再互相污染。

### 建议分层

1. **Conversation Context**
   - 最近对话
   - 模型直接输入

2. **Execution Scratchpad**
   - 当前轮推理所需临时状态

3. **Artifacts**
   - 搜索原始结果
   - 网页内容
   - 天气原始 JSON
   - 长工具输出

4. **Long-term Memory**
   - 用户偏好
   - 项目知识
   - 常见失败案例

### 需要做的事情

- ContextManager 不再只做截断压缩
- 增加 artifact 存储与引用机制
- 工具结果默认保存为 artifact，主上下文只放摘要
- 逐步把 MemoryManager 从“会话状态表”升级成长期记忆入口

### 验收标准

- [ ] 长工具输出不直接塞进主上下文
- [ ] 上下文压缩不再只依赖字符长度
- [ ] 历史轮次 50+ 仍可稳定运行

---

## 阶段 4：权限与安全升级

### 目标

让工具权限管理达到可追踪、可恢复、可审计。

### 需要增强

- 权限请求持久化
- 授权结果缓存
- 对话恢复后继续执行
- 规则级自动批准机制
- 审批日志记录

### 权限分级建议

- `auto`
- `ask_once`
- `ask_always`
- `deny`

### 验收标准

- [ ] 权限请求可恢复
- [ ] 用户审批后可继续执行原任务
- [ ] 授权策略可配置

---

## 阶段 5：可观测性与测试体系

### 目标

降低问题定位成本，使框架具备持续演进能力。

### 建议增加的观测字段

- `run_id`
- `conversation_id`
- `model_name`
- `tool_name`
- `tool_call_id`
- `iteration`
- `latency_ms`
- `stop_reason`
- `error_type`

### 测试建议

必须建立以下回归测试：

1. 豆包流式 tool_call 分片组装测试
2. assistant/tool 回填协议测试
3. 异步 StructuredTool 执行测试
4. 确定性工具结果直出测试
5. 天气工具结果格式化测试
6. 前端 SSE 消费测试
7. ORM 生命周期边界测试

### 验收标准

- [ ] 关键链路有自动化回归
- [ ] 新问题能通过 run_id 快速追踪
- [ ] 生产日志可以支持问题复盘

---

## 阶段 6：前端渲染分级

### 目标

避免所有 assistant 消息都走同一套 Markdown 渲染策略。

### 建议 render_mode

- `markdown`
- `plain_text`
- `tool_card`
- `structured_table`

### 适用场景

- 普通回答: `markdown`
- 天气、时间、数据库查询: `plain_text`
- 工具执行过程: `tool_card`
- 检索结果集合: `structured_table`

### 验收标准

- [ ] 工具结果不再因 Markdown 产生样式漂移
- [ ] 前端可根据消息元数据选择渲染器

---

## 六、优先级排序

### P0：必须优先完成

- 阶段 1 稳定性内核升级
- 阶段 2 AgentHarness 状态机化
- 阶段 5 可观测性与核心回归测试

### P1：紧随其后

- 阶段 3 上下文、Artifact、记忆分层
- 阶段 6 前端渲染分级

### P2：后续增强

- 阶段 4 权限与安全升级

---

## 七、实施建议

建议不要一次性大改，而是按以下顺序推进：

1. 先完成事件协议、工具元数据、确定性结果直出
2. 再将 Agent Loop 状态机化
3. 然后补结构化 trace 和回归测试
4. 最后做上下文、artifact、前端分级渲染

这样能在不打断当前功能的前提下，逐步向成熟框架靠拢。

---

## 八、成功标准

当以下条件大部分满足时，可以认为框架接近成熟 Agent 平台：

- [ ] 关键执行流都是显式状态机
- [ ] 工具元数据、执行器、formatter 完全统一
- [ ] 确定性结果默认不被模型污染
- [ ] 长上下文可控，不依赖简单截断
- [ ] 每次执行都有 run_id / stop_reason / trace
- [ ] 关键链路均有自动化回归测试
- [ ] 前端根据消息类型区分渲染方式

---

## 九、相关参考

- `backend/harness/agent_harness.py`
- `backend/harness/tool_registry.py`
- `backend/harness/context_manager.py`
- `backend/harness/memory_manager.py`
- `backend/harness/permission_service.py`
- `backend/orchestrator.py`
- `frontend-vue/src/views/ChatView.vue`
- 当日天气工具调用历史修复记录（已并入当前精简历史）

---

## 十、结论

当前框架已经具备继续演进的基础，但离成熟 Agent 平台还有一段距离。最关键的不是继续堆更多功能，而是优先补齐：

- 状态机
- 工具平台化
- 确定性结果治理
- 可观测性
- 自动化回归

只要这五个基础层补齐，后续再叠加多智能体、长期记忆、自我改进，才不会持续放大复杂度。
