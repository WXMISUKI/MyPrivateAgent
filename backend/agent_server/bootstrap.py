"""Bootstrap helpers for the server package."""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect, text

try:
    from config import DB_HOST, DB_MODE, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DATABASE_URL, LOCAL_DATA_DIR, SQLITE_PATH
    from database import Base, engine
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import DB_HOST, DB_MODE, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DATABASE_URL, LOCAL_DATA_DIR, SQLITE_PATH
    from backend.database import Base, engine


logger = logging.getLogger(__name__)


def load_environment() -> Path:
    """Load environment variables from the project root .env file."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path)
    logger.info("已加载环境变量文件: %s", env_path)
    return env_path


def init_database() -> None:
    """Ensure the configured database and tables exist."""
    if DB_MODE == "mysql":
        import pymysql

        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                logger.info("数据库 '%s' 已创建或已存在", DB_NAME)
        finally:
            connection.close()
    else:
        Path(LOCAL_DATA_DIR).mkdir(parents=True, exist_ok=True)
        logger.info("使用本地 SQLite 存储: %s", SQLITE_PATH)

    Base.metadata.create_all(bind=engine)
    _ensure_feedback_uniqueness_constraint()
    logger.info("存储表结构已创建，模式=%s，URL=%s", DB_MODE, DATABASE_URL)


def _ensure_feedback_uniqueness_constraint() -> None:
    """Best-effort unique constraint setup for feedback idempotency."""
    constraint_name = "uq_message_feedback_conv_msg_user"
    inspector = inspect(engine)

    table_names = set(inspector.get_table_names())
    if "message_feedback" not in table_names:
        return

    unique_constraints = inspector.get_unique_constraints("message_feedback")
    if any(item.get("name") == constraint_name for item in unique_constraints):
        return

    with engine.begin() as connection:
        duplicate_row = connection.execute(
            text(
                """
                SELECT conversation_id, message_id, user_id, COUNT(*) AS cnt
                FROM message_feedback
                WHERE message_id IS NOT NULL AND user_id IS NOT NULL
                GROUP BY conversation_id, message_id, user_id
                HAVING cnt > 1
                LIMIT 1
                """
            )
        ).fetchone()
        if duplicate_row:
            logger.warning(
                "message_feedback 存在重复数据，跳过唯一约束创建，请先清理重复记录: %s",
                dict(duplicate_row._mapping),
            )
            return

        connection.execute(
            text(
                f"""
                ALTER TABLE message_feedback
                ADD CONSTRAINT {constraint_name}
                UNIQUE (conversation_id, message_id, user_id)
                """
            )
        )
        logger.info("已创建反馈唯一约束: %s", constraint_name)
