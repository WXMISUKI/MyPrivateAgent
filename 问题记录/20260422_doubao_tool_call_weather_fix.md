# 豆包工具调用与天气查询问题复盘

## 文档信息
- 创建日期: 2026-04-22
- 状态: 已解决
- 影响范围: 豆包模型工具调用、天气查询、流式对话、自学习记录

---

## 一、问题现象

在使用豆包模型询问“今天舟山什么天气”时，系统先后出现了以下问题：

1. 工具调用后最终响应为空，前端表现为超时或无答案
2. 工具调用反复重试，形成多轮无效调用
3. 天气工具接入后，执行报错 `StructuredTool does not support sync invocation.`
4. 天气结果虽然能查到，但最终回复中的日期、温度范围、风速等数值被模型改写，出现格式缺损和数据失真
5. 流式结束后，自学习记录报错：`User is not bound to a Session`

---

## 二、根因分析

### 2.1 工具调用协议闭环缺失

豆包函数调用需要严格遵循：

`user -> assistant(tool_calls) -> tool -> assistant(final)`

原实现中执行完工具后只追加了 `ToolMessage`，没有把带 `tool_calls` 的 `assistant` 消息补回上下文，导致第二轮生成最终答案时上下文结构不合法。

### 2.2 流式 tool_call 解析不完整

豆包流式返回的 `tool_calls` 与 `invalid_tool_calls` 是分块的。原始实现对对象型 chunk 支持不足，导致工具调用经常依赖补发 `ainvoke` 才能勉强恢复，增加了时延和复杂度。

### 2.3 异步 StructuredTool 被错误同步执行

当前 `search` 是 LangChain `StructuredTool`，且内部实现为异步天气查询。原来的执行器优先走同步 `invoke()`，直接触发：

`StructuredTool does not support sync invocation.`

### 2.4 确定性工具结果被模型二次改写

天气查询本质上是确定性强的数据读取。系统原本在拿到天气工具结果后，再让模型做第二轮自然语言总结。豆包会把结构化文本重新组织成自然语言，这一步可能引入：

- 日期截断
- 温度范围连接符丢失
- 风速数值被错误改写
- Markdown 样式漂移

### 2.5 前端 Markdown 渲染放大了格式漂移

前端消息正文默认通过 `marked` 渲染为 HTML。模型一旦在第二轮输出列表、短横线或接近 Markdown 的结构，界面就会出现项目符号、日期样式异常等视觉问题。

### 2.6 ORM 对象跨流式生命周期失效

`current_user` 在流式生成结束后已脱离有效 Session，后续自学习模块再次读取 `current_user.id` 时触发 ORM 绑定错误。

---

## 三、修复动作

### 3.1 修复 AgentHarness 工具调用主链路

- 补齐 `assistant(tool_calls)` 消息回填
- 完善豆包流式 `tool_calls` / `invalid_tool_calls` 分块组装
- 仅在“既无正文也无工具调用”时才允许 fallback 到 `ainvoke`
- 统一规范化工具调用参数

### 3.2 修复工具执行器

- `StructuredTool` 优先使用 `ainvoke()`
- 同步工具才走 `invoke()`
- 对空参数片段（如 `}`）增加解析兜底

### 3.3 接入真实天气服务

- 新增共享服务 `backend/services/weather_service.py`
- 使用 Open-Meteo 查询真实天气
- 城市识别、天气码映射、未来三天摘要统一收口到服务层
- `search_tool.py`、`langchain_tools.py`、`routers/chat.py` 三处天气逻辑改为复用共享服务

### 3.4 确定性天气结果直出

对于单次天气查询：

- 若工具结果为标准天气结果格式
- 则直接返回工具结果
- 跳过第二轮模型改写

此举显著降低了天气数据在模型总结过程中被污染的风险。

### 3.5 优化天气结果格式

将天气输出调整为稳定的纯文本结构：

- 固定标题
- 单行单字段
- 日期统一为 `YYYY/MM/DD`
- 温度范围使用“至”而非波浪线

这样更不容易被 Markdown 或模型自然语言重写破坏。

### 3.6 修复自学习记录 Session 问题

在流式开始前先提取 `current_user_id` 为普通值，避免在流式结束后使用脱离 Session 的 ORM 实例。

---

## 四、最终结果

修复后，豆包查询“今天舟山什么天气”可以稳定完成：

1. 正确解析并执行 `search` 工具调用
2. 能通过真实天气接口获取舟山天气
3. 最终答案不再空白、不再死循环
4. 天气数值和日期不再因模型二次改写而失真
5. 自学习记录不再因 `User` Session 生命周期报错

---

## 五、经验总结

### 5.1 确定性工具结果不要默认交给模型重写

天气、时间、数据库查询、检索摘要等结果，优先直接返回或做轻量模板化格式化。模型二次改写只适合开放性总结，不适合高精度数据回写。

### 5.2 Tool schema、executor、formatter 必须统一收口

工具定义、执行、输出格式如果散落在多个模块，问题会在不同层级重复出现。后续所有工具都应采用单一事实来源。

### 5.3 流式工具调用必须有回归测试

后续新增或修改工具调用链路时，至少要覆盖：

- tool_call 分片组装
- assistant/tool 回填协议
- 异步工具执行
- 确定性工具直出
- SSE 前端消费

### 5.4 ORM 实例不要跨长生命周期异步边界使用

流式场景下只传递原始值（如 `user_id`、`conversation_id`），不要在流尾阶段继续依赖 ORM 实例。

---

## 六、后续预防清单

- [ ] 所有新工具声明是否为确定性结果
- [ ] 确定性工具是否定义了统一 formatter
- [ ] 新工具是否支持异步执行路径
- [ ] tool_call 是否有流式分片回归测试
- [ ] 是否避免把 ORM 实例穿透到流尾逻辑
- [ ] 前端是否根据消息类型区分 Markdown 与纯文本渲染

---

## 七、相关文件

- `backend/harness/agent_harness.py`
- `backend/harness/tools/langchain_tools.py`
- `backend/harness/tools/search_tool.py`
- `backend/services/weather_service.py`
- `backend/routers/chat.py`
- `frontend-vue/src/views/ChatView.vue`

---

## 八、建议

本次问题已经暴露出当前框架在以下方面仍需系统性提升：

- Agent 状态机建模
- 工具平台化
- 确定性结果渲染策略
- 结构化事件协议
- 测试与可观测性

这些内容已在 `20260422_harness_maturity_upgrade_plan.md` 中进一步展开。
