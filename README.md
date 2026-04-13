# MyPrivateAgent 项目设计文档

## 一、项目概述

**项目名称**：MyPrivateAgent  
**项目类型**：私有 AI 对话助手 Web 应用  
**核心功能**：用户注册登录、多模型对话、会话历史管理  
**目标用户**：个人用户，本地部署使用

---

## 二、技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | FastAPI + SQLAlchemy + Pydantic |
| 数据库 | MySQL (localhost:3306) |
| 认证 | JWT Token + HTTPOnly Cookie |
| 前端 | HTML + CSS + JavaScript (原生) |
| AI 对话 | LangGraph + Ollama (LLM) |
| 密码加密 | bcrypt |

---

## 三、数据库设计

### 3.1 数据库名称
```
MyPrivateAgent
```

### 3.2 表结构

#### 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT (主键, 自增) | 用户ID |
| username | VARCHAR(50) | 用户名 (唯一) |
| password_hash | VARCHAR(255) | 加密后的密码 |
| created_at | DATETIME | 注册时间 |
| updated_at | DATETIME | 更新时间 |

#### 对话会话表 (conversations)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT (主键, 自增) | 会话ID |
| user_id | INT (外键) | 所属用户ID |
| title | VARCHAR(255) | 对话标题 |
| model_name | VARCHAR(50) | 使用的模型 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 消息表 (messages)
| 字段 |类型 | 说明 |
|------|------|------|
| id | INT (主键, 自增) | 消息ID |
| conversation_id | INT (外键) | 所属会话ID |
| role | VARCHAR(20) | 角色 (user/assistant) |
| content | TEXT | 消息内容 |
| created_at | DATETIME | 创建时间 |

---

## 四、API 接口设计

### 4.1 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/logout | 用户登出 |
| GET | /api/auth/me | 获取当前用户信息 |

### 4.2 对话接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/conversations | 获取用户所有会话 |
| POST | /api/conversations | 创建新会话 |
| GET | /api/conversations/{id} | 获取会话详情 |
| DELETE | /api/conversations/{id} | 删除会话 |
| POST | /api/chat | 发送消息并获取回复 |

### 4.3 模型接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/models | 获取可用模型列表 |

---

## 五、前端页面设计

### 5.1 页面结构

```
登录页 (login.html)
    │
    ▼
主页面 (index.html)
    ├── 顶部栏：用户名称 + 下拉菜单（退出登录）
    ├── 左侧栏：会话列表 + 新建对话按钮
    └── 右侧栏：对话窗口 + 模型选择下拉框
```

### 5.2 功能说明

1. **登录页**：用户名/密码输入，注册/登录按钮
2. **主页面**：
   - 顶部显示当前用户名
   - 点击用户名显示下拉菜单（退出登录）
   - 左侧显示历史会话列表，点击切换对话
   - 左侧"新建对话"按钮创建新会话
   - 右侧对话区域，支持流式输出
   - 模型选择下拉框切换对话模型

---

## 六、可用模型列表

| 模型名称 | 说明 |
|----------|------|
| llama3.1 | Llama 3.1 (默认) |
| deepseek-r1:7b | DeepSeek R1 |
| llava | 多模态模型 |

---

## 七、项目目录结构

```
D:\AI\AIcode\MyPrivateAgent\
├── backend/
│   ├── main.py              # FastAPI 主入口
│   ├── config.py             # 配置项
│   ├── models.py             # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py           # 数据库连接
│   ├── auth.py               # 认证逻辑
│   └── routers/
│       ├── auth.py           # 认证路由
│       ├── chat.py           # 对话路由
│       └── conversations.py # 会话路由
├── frontend/
│   ├── login.html            # 登录页
│   ├── index.html            # 主页面
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # 样式
│   │   └── js/
│   │       ├── login.js     # 登录逻辑
│   │       ├── chat.js      # 对话逻辑
│   │       └── app.js       # 主应用逻辑
│   └── templates/            # HTML 模板
├── .env                      # 环境变量
└── requirements.txt          # Python 依赖
```

---

## 八、部署步骤

### 8.1 后端启动
```bash 首次使用
cd D:\AI\AIcode\MyPrivateAgent\backend
pip install -r requirements.txt
python main.py
# 服务运行在 http://localhost:8000
```

### 8.2 前端访问
```
http://localhost:8000
```

---

## 九、安全考虑

1. 密码使用 bcrypt 加密存储
2. JWT Token 存储在 HTTPOnly Cookie 中
3. CORS 配置允许前端访问
4. 用户只能访问自己的对话记录

---

## 十、待确认事项

- [x] 数据库配置
- [x] 认证方式
- [x] 模型列表
- [x] 部署方式

---

## 十一、使用说明

### 11.1 启动服务

**前置条件：**
- MySQL 服务已启动（用户 root，密码 root）
- Ollama 服务已启动（默认 http://localhost:11434）

**启动后端：**
```bash

你的项目采用 FastAPI + Jinja2 模板架构（非真正的前后端分离），只需启动后端即可：

   conda activate langgraph-env
   cd D:\AI\AIcode\MyPrivateAgent\backend
   python main.py

  前端访问

  后端启动后，直接在浏览器访问：
   - 登录页: http://localhost:8000/login
   - 主页面: http://localhost:8000/index

  工具调用说明

### 11.2 使用流程

1. 打开浏览器访问 http://localhost:8000
2. 点击"注册"按钮创建账号
3. 登录后即可使用对话功能
4. 左侧栏可以查看历史对话和新建对话
5. 右上角可以切换用户模型
6. 点击用户名可退出登录

### 11.3 技术细节

- 后端：FastAPI + SQLAlchemy + MySQL
- 前端：原生 HTML/CSS/JS
- 认证：JWT Token (HTTPOnly Cookie)
- 密码加密：bcrypt
- AI 对话：LangGraph + Ollama

---

*文档创建时间：2026-03-08*
*最后更新时间：2026-03-08*
