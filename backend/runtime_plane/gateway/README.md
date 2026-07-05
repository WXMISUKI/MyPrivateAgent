# Intent Router / Runtime Selector

## 定位

运行层的入口路由能力。

## 组件

- **IntentRouter**: 意图识别，将用户请求路由到目标 agent_id
- **RuntimeSelector**: 运行时选择，根据 agent manifest 配置选择执行框架（langgraph / agentrun / adk / local）

## 路由流程

```
用户请求 → IntentRouter (识别 agent_id)
         → AgentRegistry (查找 agent manifest)
         → RuntimeSelector (选择执行框架)
         → ExecutionAdapter (翻译并执行)
         → ExecutionEvent stream (标准化事件)
         → Control Plane (治理消费)
```

## 当前状态

**骨架占位**。路由逻辑将在 Stage 1 或之后实现。
