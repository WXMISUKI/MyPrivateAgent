# Framework Phase 30 实施记录

## 日期
2026-04-24

## 主题
Starter / Demo Productization：`weather_demo`、`knowledge_demo` 与 Starter Guide

## 背景
前几个阶段已经把框架的核心能力做到了较成熟的层次：

- runtime state / event protocol
- tool metadata / artifacts / cards / cache
- app factory / auth provider / preset
- runtime knowledge injection / governance
- 前端调试视图

但这些能力仍然更多体现为“一个很强的项目”，还不够像“别人可以直接套用的 demo framework”。

## 本次目标

让这套框架更接近真正的 starter/demo 形态：

1. 提供更明确的场景化 preset
2. 提供最小示例入口
3. 提供 starter 文档

## 本次改动

### 1. 新增两个 starter-oriented preset
- 文件：`backend/agent_server/config.py`
- 文件：`backend/agent_server/__init__.py`

新增：
- `weather_demo`
- `knowledge_demo`

#### `weather_demo`
适合：
- 天气
- 实时查询
- 确定性工具直出
- structured card 展示

路由组：
- `auth`
- `core`
- `permissions`

#### `knowledge_demo`
适合：
- 知识问答
- 学习治理
- runtime knowledge 注入

路由组：
- `auth`
- `core`
- `learning`
- `permissions`

二者都默认：
- 使用 Vue SPA 作为 UI

### 2. 新增 starter 示例入口
- 文件：`examples/__init__.py`
- 文件：`examples/weather_demo_app.py`
- 文件：`examples/knowledge_demo_app.py`

现在可以直接使用：
- `examples.weather_demo_app:app`
- `examples.knowledge_demo_app:app`

这让“新垂域 agent”的起步方式更清晰，不再只能从主应用入口改起。

### 3. 新增 Starter Guide
- 文件：`docs/agent_framework_starter_guide.md`

内容包括：
- 如何选择 preset
- 如何运行 starter 示例
- 如何构建新垂域 agent
- 最小 domain checklist
- 框架代码与领域代码的边界

### 4. Demo Guide 更新
- 文件：`docs/agent_framework_demo_guide.md`

补充：
- 新增 preset 说明
- starter guide 链接
- 示例入口链接

## 测试

### 更新
- `tests/agent_framework/test_agent_server_app.py`

新增覆盖：
- `weather_demo` preset
- `knowledge_demo` preset
- preset registry 列表更新

## 验证结果
- `test_agent_server_app` 通过
- 完整后端测试：63 项通过
- 示例入口 `py_compile` 通过

## 结果
这一步之后，项目已经更接近真正的“可套用 demo framework”：

- 不再只有一个总入口
- 有清晰的 starter preset
- 有可直接运行的示例 app
- 有面向复用的 starter 文档

## 下一步建议

优先继续做两件事：

1. **用户反馈接入 runtime effect**
   - 把用户正负反馈与 runtime knowledge effect 关联
   - 为自动晋升 / 自动回滚提供信号

2. **更强的 starter 模板化**
   - 提供 domain service / tool / card schema 的模板文件
   - 让新 agent 不只是“照着文档写”，而是“从模板改”
