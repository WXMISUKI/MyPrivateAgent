from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
import pymysql
from dotenv import load_dotenv
import os
from pathlib import Path

# 加载环境变量
load_dotenv()

from database import engine, Base
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from routers import auth, conversations, chat, skills

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 静态文件和模板路径
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"

app = FastAPI(title="MyPrivateAgent", description="私有 AI 对话助手")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Jinja2 模板
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 注册路由
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(skills.router)


def init_database():
    """初始化数据库"""
    # 首先连接到 MySQL 服务器（不指定数据库）
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 '{DB_NAME}' 已创建或已存在")
    finally:
        connection.close()

    # 创建表
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")


@app.on_event("startup")
def on_startup():
    """应用启动时初始化数据库"""
    init_database()


@app.get("/")
def root():
    """根路径重定向到登录页"""
    return RedirectResponse(url="/login")


@app.get("/login")
def login_page():
    """登录页"""
    return templates.TemplateResponse("login.html", {"request": {}})


@app.get("/index")
def index_page():
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": {}})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
