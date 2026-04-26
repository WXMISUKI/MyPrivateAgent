from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    from config import DATABASE_URL, DB_MODE, LOCAL_DATA_DIR
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import DATABASE_URL, DB_MODE, LOCAL_DATA_DIR

if DB_MODE != "mysql":
    Path(LOCAL_DATA_DIR).mkdir(parents=True, exist_ok=True)

# 创建引擎
engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_kwargs)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
