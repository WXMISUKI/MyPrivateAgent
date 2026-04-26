# 当前框架建设进度总结

## 日期
2026-04-24

## 目标背景
本轮工作的主线，不再是单点修 Bug，而是把当前项目从“能跑的私有智能体项目”逐步收口为“可复用、可装配、可评估、可扩展的通用 Agent Demo Framework”。

## 已完成的核心进度

### 1. 执行主链已基本收口
- `AgentHarness + Orchestrator + ChatService` 已成为主执行链。
- 豆包工具调用、天气查询、流式事件解析、structured card 输出已打通。
- 天气类查询已支持工具直出，避免二次模型改写带来的延迟和格式漂移。

### 2. 框架层已经初步抽离成可复用结构
- 已形成 `backend/agent_framework/` 通用运行时层。
- 已形成 `backend/agent_server/` server 装配层。
- `create_app()` 已支持 preset、路由组、认证 provider 等场景化装配。
- 已补 `weather_demo`、`knowledge_demo` 示例入口和 starter 文档。

### 3. 运行时可观测性明显增强
- 前端已能看到 structured card。
- 已支持 runtime knowledge 注入信息展示。
- 已支持 tool execution trace、cache hit、duration、result source 等调试信息展示。
- 这部分已经接近成熟 harness/workbench 的调试视角。

### 4. 自学习闭环已打通最小后端链路
- 已有 `runtime_knowledge_effect` 追踪。
- 已新增会话反馈模型、反馈 API、负反馈转 `Learning` 的后端闭环。
- 后端已经具备“反馈 -> effect -> learning”的最小能力。

### 5. 工程化基础比之前成熟很多
- 已补一批后端测试，覆盖 app factory、runtime、card schema、tool cache、service 层等。
- 已有 starter/demo 文档与阶段实施记录，项目不再完全依赖口头同步。

## 当前正在进行但尚未完全收口的部分

### 1. 前端反馈入口只完成了一半
- `frontend-vue/src/stores/conversation.js` 已开始加入 `submitMessageFeedback()`、`feedbackReasons` 等能力。
- 但聊天界面的点赞/点踩、原因选择、反馈状态展示、与 runtime knowledge 命中信息联动，还没有完整落到 UI。
- 这意味着：后端闭环已具备，前端闭环还未完成。

### 2. 反馈效果分析层还没建立
- 当前能记录单次反馈。
- 但还没有按 `prompt_key`、`practice_id`、`scope` 聚合命中效果、负反馈率、回滚候选。
- 也还没有独立的管理页或统计接口。

## 还没有完成的关键收口项

### 1. 真正的前端 Workbench 闭环
- 消息级反馈入口
- 本次命中的 runtime knowledge 可回看
- 反馈后即时显示已关联的 effect / learning

### 2. 效果治理与运营视图
- feedback analytics API
- practice/prompt 维度统计
- 回滚建议和低质量知识识别

### 3. 端到端自动化验证
- `/api/chat` SSE 端到端测试
- tool -> card -> done -> feedback -> learning 全链路测试
- 前端联调级测试仍然缺失

### 4. 真正的模板化复用能力
- 现在已有 starter guide 和 demo preset
- 但还缺真正的 domain scaffold/template，暂时还不到“像 npm 包一样一装即用”的程度

## 当前结论
如果按成熟度判断，项目已经从“单项目应用”走到了“可复用框架雏形”，而且后端基础设施已经比较像成熟 harness。

但若目标是接近 Claude Code / 通用 harness/workbench 级别，还差最后几层收口：
- 前端反馈与调试闭环
- 效果分析与治理层
- 端到端自动化测试
- starter 模板化脚手架

## 下一步建议顺序
1. 先完成前端反馈入口与 runtime effect 联动。
2. 再补 feedback analytics 接口和聚合统计。
3. 然后补一条完整的端到端测试链。
4. 最后再抽象 domain scaffold，把这套框架真正产品化。
