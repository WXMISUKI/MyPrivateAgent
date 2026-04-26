# MyPrivateAgent 框架抽离 Phase 6 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：将结构化卡片从聊天页内联模板中抽离为可复用组件，形成通用 renderer 入口

---

## 本次实施范围

本轮目标不是继续增加新卡片类型，而是先把已经落地的天气卡片做对组件边界：

1. 新增通用卡片入口组件
2. 新增天气卡片子组件
3. 让 `ChatView` 只负责挂载，不负责展开具体卡片模板

---

## 新增组件

### 1. 通用卡片入口

新增：

- `frontend-vue/src/components/cards/AgentStructuredCard.vue`

职责：

- 根据 `card.kind` 选择具体渲染组件
- 当前先支持 `weather`

这意味着后续再接：

- stock
- retrieval_summary
- timeline
- metrics

时，只需要继续扩展 `kind` 分支，而不必再修改聊天页主体模板。

### 2. 天气卡片子组件

新增：

- `frontend-vue/src/components/cards/WeatherCard.vue`

职责：

- 接收统一 `card` 数据
- 支持 `compact` 模式
- 自带本地样式，不再依赖 `ChatView` 页面样式

---

## 页面层改动

`frontend-vue/src/views/ChatView.vue`

已完成以下收口：

1. assistant 消息卡片改为：
   - `<AgentStructuredCard :card=\"msg.cardData\" />`
2. tool result 卡片改为：
   - `<AgentStructuredCard :card=\"tool.cardData\" compact />`
3. 页面内原本写死的 weather card 模板已移除
4. 页面内原本写死的 weather card 样式已移除

现在 `ChatView` 只关心：

- 是否存在 structured card
- 在什么位置挂载卡片

而不再关心每一种卡片的细节 UI。

---

## 本轮收益

1. 结构化卡片开始具备真正复用性
2. `ChatView` 复杂度进一步下降
3. 后续新增卡片类型的修改范围更小、更稳定
4. renderer 机制开始从“页面特判”演进成“组件分发”

---

## 验证结果

本轮验证包括：

1. Python 测试：

```bash
python -m unittest tests.agent_framework.test_provider_registry tests.agent_framework.test_adapters tests.agent_framework.test_events tests.agent_framework.test_weather_cards
```

结果：9 个测试全部通过

2. 前端构建：

```bash
cmd /c npm run build
```

结果：构建成功

---

## 当前限制

1. `AgentStructuredCard` 目前仅支持 `weather`
2. 还没有前端组件级自动化测试
3. 还没有 card schema 注册表，只有 `kind` 分发入口

---

## 下一阶段建议

建议第七步优先做：

1. 给 structured card 增加 schema 注册表
2. 让后端工具元数据和前端卡片类型建立更明确映射
3. 继续把 artifact / tool result 的展示组件化
4. 开始准备 monorepo/package 化目录迁移草案
