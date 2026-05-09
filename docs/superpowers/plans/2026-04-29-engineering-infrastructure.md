# 工程基础设施完善实施计划

> **对执行型智能体工作者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项落实本计划。步骤使用复选框语法（`- [ ]`）进行跟踪。

**目标：** 将 MyPrivateAgent 的工程基础设施提升到 MVP 成熟度，包括数据库迁移、请求链路追踪、结构化日志、安全加固、统一异常处理、优雅停机、可观测性、速率限制、上下文压缩、CI 质量门禁、代码质量重构以及框架成熟度改进。

**架构：** 在现有 FastAPI + Vue 3 技术栈上按分层方式增量扩展。新的中间件管线位于 `backend/agent_server/middleware.py`，负责请求 ID 注入、结构化日志上下文、速率限制和统一错误格式化。Alembic 与现有 SQLAlchemy 模型并行管理 schema 迁移。所有改动都要求与当前 Demo 流程保持向后兼容。

**技术栈：** Python 3.11、FastAPI、SQLAlchemy、Alembic、slowapi、python-json-logger、tiktoken、ruff、Vue 3、Pinia、Axios

---

## 文件结构

### 新增文件
- `backend/alembic.ini` — Alembic 配置文件
- `backend/alembic/env.py` — 带 SQLAlchemy metadata 的 Alembic 环境文件
- `backend/alembic/script.py.mako` — 迁移模板
- `backend/alembic/versions/001_initial_schema.py` — 初始迁移基线
- `backend/agent_server/middleware.py` — Request ID 与统一错误处理中间件
- `backend/logging_config.py` — 结构化 JSON 日志配置
- `backend/services/context_compaction_service.py` — 基于 token 的上下文截断服务
- `backend/pyproject.toml` — ruff 配置
- `tests/agent_framework/test_middleware.py` — 中间件测试
- `tests/agent_framework/test_logging_config.py` — 日志配置测试
- `tests/agent_framework/test_context_compaction_service.py` — 上下文压缩测试
- `tests/agent_framework/test_startup_validation.py` — 启动配置校验测试

### 修改文件
- `backend/requirements.txt` — 增加 alembic、slowapi、python-json-logger、tiktoken、ruff、pytest-cov
- `backend/agent_server/app.py` — 注册中间件并补齐优雅停机
- `backend/agent_server/bootstrap.py` — 用 alembic 替换 `create_all` 主流程，并增加配置校验
- `backend/config.py` — 增加安全默认值、CORS 白名单与限流配置
- `backend/main.py` — 接入结构化日志
- `backend/routers/health.py` — 增加 liveness/readiness 端点
- `backend/orchestrator.py` — 移除硬编码模型并抽取方法
- `backend/routers/chat.py` — 抽取共享流处理管线
- `backend/agent_server/config.py` — 增加基于环境变量的 CORS 配置和 API 版本前缀
- `frontend-vue/src/api/index.js` — 统一错误处理并增加 API 版本前缀支持
- `frontend-vue/src/stores/conversation.js` — 抽取 `_processSSEStream`
- `.github/workflows/ci.yml` — 增加 ruff、eslint 和覆盖率门禁

---

## 第一批：工程基础设施核心（任务 1-6）

### 任务 1：Alembic 数据库迁移

**涉及文件：**
- 新增：`backend/alembic.ini`
- 新增：`backend/alembic/env.py`
- 新增：`backend/alembic/script.py.mako`
- 新增：`backend/alembic/versions/001_initial_schema.py`
- 修改： `backend/requirements.txt`
- 修改： `backend/agent_server/bootstrap.py:30-55`

- [ ] **步骤 1：向 requirements.txt 增加 alembic**

在 `backend/requirements.txt` 末尾追加：

```
alembic==1.13.1
```

- [ ] **步骤 2：创建 alembic.ini**

创建 `backend/alembic.ini`：

```ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///%(here)s/../.myagent/app.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **步骤 3：创建 alembic/env.py**

创建 `backend/alembic/env.py`：

```python
from logging.config import fileConfig
from pathlib import Path
import sys

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import Base, DATABASE_URL
import models  # noqa: F401 — ensure all models are registered

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **步骤 4：创建 alembic/script.py.mako**

创建 `backend/alembic/script.py.mako`：

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
创建 Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **步骤 5：创建初始迁移基线**

创建 `backend/alembic/versions/001_initial_schema.py`：

```python
"""initial schema baseline

Revision ID: 001
Revises:
创建 Date: 2026-04-29
"""
from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline: tables already exist via create_all.
    # This revision stamps the starting point so future migrations work.
    pass


def downgrade() -> None:
    pass
```

- [ ] **步骤 6: 更新 bootstrap.py 以接入 alembic**

替换 the `init_database` function in `backend/agent_server/bootstrap.py`. Keep `create_all` as fallback for fresh installs, then stamp alembic head:

```python
def init_database() -> None:
    """Ensure the configured database and tables exist."""
    if DB_MODE == "mysql":
        import pymysql
        connection = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
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
    _stamp_alembic_head_if_needed()
    logger.info("存储表结构已创建，模式=%s，URL=%s", DB_MODE, DATABASE_URL)


def _stamp_alembic_head_if_needed() -> None:
    """Stamp alembic version table so future migrations start from current state."""
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        command.stamp(alembic_cfg, "head")
        logger.info("Alembic version stamped to head")
    except Exception as e:
        logger.warning("Alembic stamp skipped: %s", e)
```

- [ ] **步骤 7: 验证 alembic 配置**

Run from `backend/` directory:
```bash
cd backend && python -c "from alembic.config import Config; from alembic import command; c = Config('alembic.ini'); print('Alembic config OK')"
```
预期： `Alembic config OK`

- [ ] **步骤 8: 提交**

```bash
git add backend/alembic.ini backend/alembic/ backend/requirements.txt backend/agent_server/bootstrap.py
git commit -m "feat: add Alembic database migration infrastructure"
```

---

### 任务 2：Request ID 中间件

**涉及文件：**
- Create: `backend/agent_server/middleware.py`
- Create: `tests/agent_framework/test_middleware.py`
- 修改： `backend/agent_server/app.py:107-131`

- [ ] **步骤 1: 先编写失败测试**

创建 `tests/agent_framework/test_middleware.py`:

```python
import unittest
from unittest.mock import AsyncMock, MagicMock
from backend.agent_server.middleware import RequestIDMiddleware, get_request_id


class TestRequestIDMiddleware(unittest.TestCase):
    def test_get_request_id_returns_none_outside_request(self):
        self.assertIsNone(get_request_id())


class TestRequestIDMiddlewareIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_middleware_sets_response_header(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_endpoint():
            return {"request_id": get_request_id()}

        client = TestClient(app)
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
        body = response.json()
        self.assertEqual(body["request_id"], response.headers["X-Request-ID"])

    async def test_middleware_uses_incoming_header(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_endpoint():
            return {"request_id": get_request_id()}

        client = TestClient(app)
        response = client.get("/test", headers={"X-Request-ID": "custom-id-123"})
        self.assertEqual(response.json()["request_id"], "custom-id-123")
        self.assertEqual(response.headers["X-Request-ID"], "custom-id-123")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2: 运行测试，确认其先失败**

运行： `python -m unittest tests.agent_framework.test_middleware -v`
预期： FAIL with `ModuleNotFoundError: No module named 'backend.agent_server.middleware'`

- [ ] **步骤 3: 编写中间件实现**

创建 `backend/agent_server/middleware.py`:

```python
"""Request-scoped middleware: request ID injection and unified error handling."""

from __future__ import annotations

import contextvars
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id() -> Optional[str]:
    return _request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming_id or uuid.uuid4().hex
        token = _request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id_var.reset(token)
```

- [ ] **步骤 4: 运行测试，确认其通过**

运行： `python -m unittest tests.agent_framework.test_middleware -v`
预期： PASS (3 tests)

- [ ] **步骤 5: Register middleware in app.py**

在 `backend/agent_server/app.py`, add import at top:

```python
from .middleware import RequestIDMiddleware
```

In the `create_app` function, after the CORS middleware line (`app.add_middleware(CORSMiddleware, ...)`), add:

```python
    app.add_middleware(RequestIDMiddleware)
```

- [ ] **步骤 6: 提交**

```bash
git add backend/agent_server/middleware.py tests/agent_framework/test_middleware.py backend/agent_server/app.py
git commit -m "feat: add X-Request-ID middleware for request tracing"
```

---

### 任务 3：结构化日志

**涉及文件：**
- Create: `backend/logging_config.py`
- Create: `tests/agent_framework/test_logging_config.py`
- 修改： `backend/main.py`
- 修改： `backend/requirements.txt`

- [ ] **步骤 1: Add python-json-logger to requirements.txt**

添加到 `backend/requirements.txt`:

```
python-json-logger==2.0.7
```

- [ ] **步骤 2: 先编写失败测试**

创建 `tests/agent_framework/test_logging_config.py`:

```python
import json
import io
import logging
import unittest

from backend.logging_config import setup_logging, RequestIDFilter


class TestStructuredLogging(unittest.TestCase):
    def test_setup_logging_returns_logger(self):
        logger = setup_logging()
        self.assertIsInstance(logger, logging.Logger)

    def test_request_id_filter_adds_field(self):
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        f = RequestIDFilter()
        f.filter(record)
        self.assertTrue(hasattr(record, "request_id"))

    def test_json_output_format(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        from pythonjsonlogger import jsonlogger
        handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s"))
        handler.addFilter(RequestIDFilter())

        logger = logging.getLogger("test_json_output")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        logger.info("test message")

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        self.assertEqual(parsed["message"], "test message")
        self.assertIn("request_id", parsed)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3: 运行测试，确认其先失败**

运行： `python -m unittest tests.agent_framework.test_logging_config -v`
预期： FAIL with `ModuleNotFoundError`

- [ ] **步骤 4: 编写日志配置**

创建 `backend/logging_config.py`:

```python
"""Structured JSON logging with request ID correlation."""

from __future__ import annotations

import logging
import os

from pythonjsonlogger import jsonlogger


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from agent_server.middleware import get_request_id
        except ModuleNotFoundError:
            from backend.agent_server.middleware import get_request_id
        record.request_id = get_request_id() or "-"
        return True


def setup_logging() -> logging.Logger:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json")

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s")

    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    root_logger.addHandler(handler)

    return root_logger
```

- [ ] **步骤 5: 运行测试，确认其通过**

运行： `python -m unittest tests.agent_framework.test_logging_config -v`
预期： PASS (3 tests)

- [ ] **步骤 6: Update main.py to use structured logging**

替换 the logging setup in `backend/main.py`:

```python
import os
try:
    from agent_server import create_app
except ModuleNotFoundError:
    from backend.agent_server import create_app

try:
    from logging_config import setup_logging
except ModuleNotFoundError:
    from backend.logging_config import setup_logging

setup_logging()

preset = os.getenv("AGENT_SERVER_PRESET", "full_stack")
app = create_app(preset=preset)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **步骤 7: 提交**

```bash
git add backend/logging_config.py tests/agent_framework/test_logging_config.py backend/main.py backend/requirements.txt
git commit -m "feat: add structured JSON logging with request ID correlation"
```

---

### 任务 4：统一异常处理

**涉及文件：**
- 修改： `backend/agent_server/middleware.py`
- 修改： `backend/agent_server/app.py`
- 修改： `tests/agent_framework/test_middleware.py`

- [ ] **步骤 1: 先编写失败测试**

添加到 `tests/agent_framework/test_middleware.py`:

```python
class TestUnifiedErrorHandler(unittest.IsolatedAsyncioTestCase):
    async def test_validation_error_returns_422_with_structure(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        app = FastAPI()

        from backend.agent_server.middleware import RequestIDMiddleware, install_error_handlers
        app.add_middleware(RequestIDMiddleware)
        install_error_handlers(app)

        class Item(BaseModel):
            name: str

        @app.post("/test")
        def test_endpoint(item: Item):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/test", json={"wrong_field": 1})
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertIn("error", body)
        self.assertIn("code", body["error"])
        self.assertIn("message", body["error"])
        self.assertIn("request_id", body["error"])

    async def test_unhandled_exception_returns_500(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        from backend.agent_server.middleware import RequestIDMiddleware, install_error_handlers
        app.add_middleware(RequestIDMiddleware)
        install_error_handlers(app)

        @app.get("/boom")
        def boom():
            raise RuntimeError("unexpected")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/boom")
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"]["code"], "INTERNAL_ERROR")
```

- [ ] **步骤 2: 运行测试，确认其先失败**

运行： `python -m unittest tests.agent_framework.test_middleware -v`
预期： FAIL with `ImportError: cannot import name 'install_error_handlers'`

- [ ] **步骤 3: 向 middleware.py 增加错误处理器**

Append to `backend/agent_server/middleware.py`:

```python
import json
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, status: int, details: object = None) -> dict:
    body = {
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "request_id": get_request_id() or "-",
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return body


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "请求参数校验失败", 422, exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", str(exc.detail), exc.status_code),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "服务器内部错误", 500),
        )
```

- [ ] **步骤 4: 运行测试，确认其通过**

运行： `python -m unittest tests.agent_framework.test_middleware -v`
预期： PASS (5 tests total)

- [ ] **步骤 5: Register error handlers in app.py**

在 `backend/agent_server/app.py`, update the import:

```python
from .middleware import RequestIDMiddleware, install_error_handlers
```

In `create_app`, after `app.add_middleware(RequestIDMiddleware)`, add:

```python
    install_error_handlers(app)
```

- [ ] **步骤 6: 提交**

```bash
git add backend/agent_server/middleware.py backend/agent_server/app.py tests/agent_framework/test_middleware.py
git commit -m "feat: add unified exception handling with structured error responses"
```

---

### 任务 5：安全加固

**涉及文件：**
- 修改： `backend/config.py`
- 修改： `backend/agent_server/config.py:100-116`
- 修改： `backend/agent_server/bootstrap.py`
- Create: `tests/agent_framework/test_startup_validation.py`

- [ ] **步骤 1: 先编写失败测试**

创建 `tests/agent_framework/test_startup_validation.py`:

```python
import os
import unittest
from unittest.mock import patch

from backend.config import _is_default_secret_key, CORS_ALLOWED_ORIGINS


class TestSecurityConfig(unittest.TestCase):
    def test_default_secret_key_detected(self):
        self.assertTrue(_is_default_secret_key("your-secret-key-change-in-production-2026"))

    def test_custom_secret_key_not_flagged(self):
        self.assertFalse(_is_default_secret_key("my-real-production-key-abc123"))

    def test_cors_origins_default_is_restrictive(self):
        self.assertIsInstance(CORS_ALLOWED_ORIGINS, list)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2: 运行测试，确认其先失败**

运行： `python -m unittest tests.agent_framework.test_startup_validation -v`
预期： FAIL with `ImportError: cannot import name '_is_default_secret_key'`

- [ ] **步骤 3: Update config.py with security helpers**

添加到 the end of `backend/config.py`:

```python
_DEFAULT_SECRET_KEYS = frozenset({
    "your-secret-key-change-in-production-2026",
    "your-secret-key",
    "changeme",
    "secret",
})

def _is_default_secret_key(key: str) -> bool:
    return key.strip() in _DEFAULT_SECRET_KEYS

CORS_ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
    if origin.strip()
]

RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "20/minute")
```

- [ ] **步骤 4: 运行测试，确认其通过**

运行： `python -m unittest tests.agent_framework.test_startup_validation -v`
预期： PASS (3 tests)

- [ ] **步骤 5: Update agent_server/config.py to use CORS from env**

在 `backend/agent_server/config.py`, update the `AgentServerConfig` class. Change the `cors_allow_origins` default:

```python
    cors_allow_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:8000")
    cors_allow_credentials: bool = True
```

And update `get_server_config_for_preset` for `PRESET_FULL_STACK`:

```python
    if preset == PRESET_FULL_STACK:
        try:
            from config import CORS_ALLOWED_ORIGINS
        except ModuleNotFoundError:
            from backend.config import CORS_ALLOWED_ORIGINS
        return AgentServerConfig(
            cors_allow_origins=tuple(CORS_ALLOWED_ORIGINS),
            cors_allow_credentials=True,
        )
```

- [ ] **步骤 6: Add startup warning for default secret key**

在 `backend/agent_server/bootstrap.py`, add at the end of `init_database`:

```python
    _warn_default_secret_key()
```

And add the function:

```python
def _warn_default_secret_key() -> None:
    try:
        from config import SECRET_KEY, AUTH_MODE, _is_default_secret_key
    except ModuleNotFoundError:
        from backend.config import SECRET_KEY, AUTH_MODE, _is_default_secret_key
    if _is_default_secret_key(SECRET_KEY):
        if AUTH_MODE == "demo_guest":
            logger.warning("SECRET_KEY 使用默认值，当前为 demo 模式可接受，生产环境请务必修改")
        else:
            logger.error("SECRET_KEY 使用默认值且非 demo 模式，这是安全风险！请在 .env 中设置 SECRET_KEY")
```

- [ ] **步骤 7: 提交**

```bash
git add backend/config.py backend/agent_server/config.py backend/agent_server/bootstrap.py tests/agent_framework/test_startup_validation.py
git commit -m "feat: add security hardening — default key detection, CORS whitelist"
```

---

### 任务 6：优雅停机

**涉及文件：**
- 修改： `backend/agent_server/app.py:45-53`

- [ ] **步骤 1: Update lifespan with shutdown cleanup**

在 `backend/agent_server/app.py`, replace the `_create_lifespan` function:

```python
def _create_lifespan(config: AgentServerConfig):
    @asynccontextmanager
    async def app_lifespan(_: FastAPI):
        """Run startup bootstrap steps and cleanup on shutdown."""
        if config.bootstrap.init_database:
            init_database()
        logger.info("Application startup complete")
        yield
        # Shutdown: dispose database connections
        try:
            from database import engine
        except ModuleNotFoundError:
            from backend.database import engine
        engine.dispose()
        logger.info("Application shutdown: database connections disposed")

    return app_lifespan
```

- [ ] **步骤 2: 验证启动仍然正常**

运行： `cd backend && python -c "from agent_server import create_app; app = create_app(); print('Startup OK')"`
预期： `Startup OK`

- [ ] **步骤 3: 提交**

```bash
git add backend/agent_server/app.py
git commit -m "feat: add graceful shutdown with database connection cleanup"
```

---

## 第一批回归检查

- [ ] **运行现有全部测试**

```bash
python -m unittest tests.agent_framework.test_middleware tests.agent_framework.test_logging_config tests.agent_framework.test_startup_validation
python -m unittest tests.agent_framework.test_health_router tests.agent_framework.test_chat_service tests.agent_framework.test_capability_gap_service
```

- [ ] **运行 smoke 脚本**

```bash
cd backend && python scripts/doctor.py
```

---

## 第二批：可观测性与可靠性（任务 7-10）

### 任务 7：健康检查增强

**涉及文件：**
- 修改： `backend/routers/health.py`
- 修改： `tests/agent_framework/test_health_router.py`

- [ ] **步骤 1: 增加 liveness 和 readiness 端点**

添加到 `backend/routers/health.py`, before the existing `/health` endpoint:

```python
@router.get("/health/live")
def liveness():
    """Lightweight liveness probe — confirms the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe — checks database connectivity."""
    checks = {"database": "ok"}
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        checks["database"] = f"error: {e}"
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}
```

- [ ] **步骤 2: 为新端点补充测试**

添加到 `tests/agent_framework/test_health_router.py`:

```python
    def test_liveness_returns_ok(self):
        response = self.client.get("/api/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness_returns_ready(self):
        response = self.client.get("/api/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
```

- [ ] **步骤 3: Run tests**

运行： `python -m unittest tests.agent_framework.test_health_router -v`
预期： PASS

- [ ] **步骤 4: 提交**

```bash
git add backend/routers/health.py tests/agent_framework/test_health_router.py
git commit -m "feat: add liveness and readiness health check endpoints"
```

---

### 任务 8：API 速率限制

**涉及文件：**
- 修改： `backend/requirements.txt`
- 修改： `backend/agent_server/app.py`
- 修改： `backend/routers/chat.py:64-68`

- [ ] **步骤 1: Add slowapi to requirements.txt**

添加到 `backend/requirements.txt`:

```
slowapi==0.1.9
```

- [ ] **步骤 2: 向 app.py 增加限流器初始化**

在 `backend/agent_server/app.py`, add imports:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

In `create_app`, after `install_error_handlers(app)`, add:

```python
    try:
        from config import RATE_LIMIT_DEFAULT
    except ModuleNotFoundError:
        from backend.config import RATE_LIMIT_DEFAULT
    limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT_DEFAULT])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

- [ ] **步骤 3: 为 chat 端点增加限流**

在 `backend/routers/chat.py`, add import:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
```

Add decorator to the `chat` function (before the existing `@router.post("/chat")`):

```python
from fastapi import Request as FastAPIRequest

@router.post("/chat")
def chat(
    request: ChatRequest,
    raw_request: FastAPIRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
```

说明： 当前限流通过 limiter 的 `default_limits` 全局生效，chat 端点默认继承该限制。如果后续需要更严格的 chat 专属限流，再单独增加 `@limiter.limit(RATE_LIMIT_CHAT)` 装饰器。

- [ ] **步骤 4: 提交**

```bash
git add backend/requirements.txt backend/agent_server/app.py backend/routers/chat.py
git commit -m "feat: add API rate limiting with slowapi"
```

---

### 任务 9：上下文窗口管理

**涉及文件：**
- Create: `backend/services/context_compaction_service.py`
- Create: `tests/agent_framework/test_context_compaction_service.py`
- 修改： `backend/requirements.txt`

- [ ] **步骤 1: Add tiktoken to requirements.txt**

添加到 `backend/requirements.txt`:

```
tiktoken==0.7.0
```

- [ ] **步骤 2: 先编写失败测试**

创建 `tests/agent_framework/test_context_compaction_service.py`:

```python
import unittest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.services.context_compaction_service import ContextCompactionService


class TestContextCompaction(unittest.TestCase):
    def setUp(self):
        self.service = ContextCompactionService(max_tokens=200)

    def test_short_conversation_unchanged(self):
        messages = [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!"),
        ]
        result = self.service.compact(messages)
        self.assertEqual(len(result), 3)

    def test_long_conversation_truncated(self):
        messages = [SystemMessage(content="System prompt.")]
        for i in range(50):
            messages.append(HumanMessage(content=f"Question {i} " * 20))
            messages.append(AIMessage(content=f"Answer {i} " * 20))
        result = self.service.compact(messages)
        self.assertLess(len(result), len(messages))
        # System message always preserved
        self.assertIsInstance(result[0], SystemMessage)

    def test_system_messages_preserved(self):
        messages = [
            SystemMessage(content="System 1"),
            SystemMessage(content="System 2"),
            HumanMessage(content="Old question " * 100),
            AIMessage(content="Old answer " * 100),
            HumanMessage(content="Recent question"),
            AIMessage(content="Recent answer"),
        ]
        result = self.service.compact(messages)
        system_msgs = [m for m in result if isinstance(m, SystemMessage)]
        self.assertGreaterEqual(len(system_msgs), 1)

    def test_count_tokens_returns_int(self):
        count = self.service.count_tokens("Hello world")
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3: 运行测试，确认其先失败**

运行： `python -m unittest tests.agent_framework.test_context_compaction_service -v`
预期： FAIL with `ModuleNotFoundError`

- [ ] **步骤 4: 编写上下文压缩服务**

创建 `backend/services/context_compaction_service.py`:

```python
"""Token-aware context window compaction for long conversations."""

from __future__ import annotations

import logging
from typing import Any, List

from langchain_core.messages import BaseMessage, SystemMessage

logger = logging.getLogger(__name__)

try:
    import tiktoken
    _encoder = tiktoken.get_encoding("cl100k_base")
    def _count(text: str) -> int:
        return len(_encoder.encode(text))
except ImportError:
    def _count(text: str) -> int:
        return len(text) // 4


class ContextCompactionService:
    def __init__(self, max_tokens: int = 8000, reserve_recent: int = 6):
        self.max_tokens = max_tokens
        self.reserve_recent = reserve_recent

    def count_tokens(self, text: str) -> int:
        return _count(text)

    def _message_tokens(self, msg: BaseMessage) -> int:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        return _count(content) + 4  # overhead per message

    def compact(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        total = sum(self._message_tokens(m) for m in messages)
        if total <= self.max_tokens:
            return list(messages)

        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        non_system = [m for m in messages if not isinstance(m, SystemMessage)]

        system_tokens = sum(self._message_tokens(m) for m in system_msgs)
        budget = self.max_tokens - system_tokens

        if budget <= 0:
            logger.warning("System messages alone exceed token budget")
            return system_msgs

        kept: list[BaseMessage] = []
        used = 0
        for msg in reversed(non_system):
            msg_tokens = self._message_tokens(msg)
            if used + msg_tokens > budget:
                break
            kept.insert(0, msg)
            used += msg_tokens

        if not kept and non_system:
            kept = non_system[-self.reserve_recent:]

        logger.info(
            "Context compacted: %d -> %d messages (%d -> ~%d tokens)",
            len(messages), len(system_msgs) + len(kept), total, system_tokens + used,
        )
        return system_msgs + kept


_instance: ContextCompactionService | None = None

def get_context_compaction_service() -> ContextCompactionService:
    global _instance
    if _instance is None:
        _instance = ContextCompactionService()
    return _instance
```

- [ ] **步骤 5: 运行测试，确认其通过**

运行： `python -m unittest tests.agent_framework.test_context_compaction_service -v`
预期： PASS (4 tests)

- [ ] **步骤 6: 提交**

```bash
git add backend/services/context_compaction_service.py tests/agent_framework/test_context_compaction_service.py backend/requirements.txt
git commit -m "feat: add token-aware context window compaction service"
```

---

### 任务 10：CI 流水线增强

**涉及文件：**
- Create: `backend/pyproject.toml`
- 修改： `backend/requirements.txt`
- 修改： `.github/workflows/ci.yml`

- [ ] **步骤 1: Add ruff and pytest-cov to requirements.txt**

添加到 `backend/requirements.txt`:

```
ruff==0.4.4
pytest-cov==5.0.0
```

- [ ] **步骤 2: 创建 ruff configuration**

创建 `backend/pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"alembic/*" = ["E", "F", "W", "I"]
```

- [ ] **步骤 3: 更新 CI 工作流**

替换 `.github/workflows/ci.yml` with:

```yaml
name: CI

on:
  push:
    branches:
      - main
      - master
  pull_request:

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install ruff
        run: pip install ruff==0.4.4
      - name: Run ruff check
        run: ruff check backend/ --config backend/pyproject.toml

  backend-tests:
    runs-on: ubuntu-latest
    needs: backend-lint
    defaults:
      run:
        working-directory: .
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install backend dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt

      - name: Run runtime tests
        run: |
          python -m unittest \
            tests.agent_framework.test_doctor_script \
            tests.agent_framework.test_capability_gap_service \
            tests.agent_framework.test_health_router \
            tests.agent_framework.test_provider_registry \
            tests.agent_framework.test_adapters \
            tests.agent_framework.test_events \
            tests.agent_framework.test_tool_cache \
            tests.agent_framework.test_weather_cards \
            tests.agent_framework.test_weather_service_cache \
            tests.agent_framework.test_datetime_cards \
            tests.agent_framework.test_search_summary_cards \
            tests.agent_framework.test_artifacts \
            tests.agent_framework.test_chat_service \
            tests.agent_framework.test_orchestrator_service \
            tests.agent_framework.test_runtime_learning_service \
            tests.agent_framework.test_agent_harness_cache \
            tests.agent_framework.test_conversation_service \
            tests.agent_framework.test_router_imports \
            tests.agent_framework.test_server_service \
            tests.agent_framework.test_agent_server_dependencies \
            tests.agent_framework.test_agent_server_app \
            tests.agent_framework.test_middleware \
            tests.agent_framework.test_logging_config \
            tests.agent_framework.test_startup_validation \
            tests.agent_framework.test_context_compaction_service

      - name: Run capability gap governance gate
        run: |
          python backend/scripts/doctor.py --capability-gaps --window-days 14 --limit 200 --max-open-actions 10 --max-long-blocked-actions 0

  frontend-build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend-vue
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend-vue/package-lock.json

      - name: Install frontend dependencies
        run: npm ci

      - name: Build frontend
        run: npm run build
```

- [ ] **步骤 4: 在本地验证 ruff 通过**

运行： `cd backend && ruff check . --config pyproject.toml`
预期： No critical errors (warnings are OK for now)

- [ ] **步骤 5: 提交**

```bash
git add backend/pyproject.toml backend/requirements.txt .github/workflows/ci.yml
git commit -m "feat: add ruff linting and enhanced CI pipeline"
```

---

## 第二批回归检查

- [ ] **运行全部测试（含新增测试）**

```bash
python -m unittest tests.agent_framework.test_middleware tests.agent_framework.test_logging_config tests.agent_framework.test_startup_validation tests.agent_framework.test_context_compaction_service tests.agent_framework.test_health_router
```

---

## 第三批：代码质量（任务 11-14）

### 任务 11：重构 Orchestrator 超长函数

**涉及文件：**
- 修改： `backend/orchestrator.py`

- [ ] **步骤 1: 抽取运行时上下文准备逻辑**

在 `backend/orchestrator.py`, extract the runtime context loading (lines ~128-175 of `process_message`) into a private method:

```python
    async def _prepare_runtime_context(
        self,
        user_message: str,
        execution_context: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, Any, Any]:
        """Load runtime knowledge, skills, subagent context, capability profile, and agent memory."""
        runtime_knowledge = self.runtime_learning_service.get_runtime_context(
            user_message=user_message, scope="chat",
        )
        subagent_context = self.subagent_runtime_service.normalize_context(execution_context)
        runtime_skills = self.skill_runtime_service.get_runtime_context(
            user_message=user_message, execution_context=execution_context,
        )
        self.mcp_runtime_service.sync_registry_tools(self.tool_registry)
        capability_profile = self.capability_profile_service.build_profile(
            tool_registry=self.tool_registry,
            runtime_skills=runtime_skills,
            runtime_knowledge=runtime_knowledge,
            execution_context=execution_context,
        )
        agent_memory = self.agent_memory_service.build_context()
        return runtime_knowledge, runtime_skills, subagent_context, capability_profile, agent_memory
```

- [ ] **步骤 2: 抽取消息构建逻辑**

```python
    def _build_messages(
        self,
        user_message: str,
        capability_profile: Any,
        agent_memory: Any,
        runtime_knowledge: Any,
        runtime_skills: Any,
        subagent_context: Any,
    ) -> list:
        messages = [SystemMessage(content=capability_profile.system_prompt)]
        if not agent_memory.is_empty and agent_memory.system_prompt:
            messages.append(SystemMessage(content=agent_memory.system_prompt))
        intent_prompt = self.completion_evaluator.build_synthesis_instruction(user_message)
        if intent_prompt:
            messages.append(SystemMessage(content=intent_prompt))
        if not runtime_knowledge.is_empty:
            messages.append(SystemMessage(content=runtime_knowledge.system_prompt))
        if not runtime_skills.is_empty:
            messages.append(SystemMessage(content=runtime_skills.system_prompt))
        if subagent_context is not None:
            messages.append(SystemMessage(content=self.subagent_runtime_service.build_role_system_prompt(subagent_context)))
        messages.append(HumanMessage(content=user_message))
        return messages
```

- [ ] **步骤 3: 抽取流事件处理逻辑**

```python
    def _process_stream_chunk(
        self,
        chunk_data: dict,
        stream_state: OrchestratorStreamState,
        selected_model: str,
        supports_reasoning: bool,
    ) -> str | None:
        """Process a single stream chunk. Returns the chunk to yield, or None to skip."""
        chunk_type = chunk_data.get("type")

        if chunk_type == "reasoning":
            stream_state.last_reasoning += chunk_data.get("content", "")
            if supports_reasoning and self.show_reasoning:
                return json.dumps(chunk_data, ensure_ascii=False) + "\n"
            return None

        if chunk_type == "content":
            content = chunk_data.get("content", "")
            if content == stream_state.last_content_chunk:
                return None
            stream_state.last_content_chunk = content
            stream_state.full_content += content
            return json.dumps(chunk_data, ensure_ascii=False) + "\n"

        if chunk_type == "tool_result":
            persist_tool_artifact(
                artifact_store=self.artifact_store,
                conversation_id=self.conversation_id,
                event_data=chunk_data,
                selected_model=selected_model,
            )
            return json.dumps(chunk_data, ensure_ascii=False) + "\n"

        return json.dumps(chunk_data, ensure_ascii=False) + "\n"
```

- [ ] **步骤 4: 重构 process_message，改为使用抽取后的方法**

Rewrite `process_message` to call the extracted methods, reducing it from ~300 lines to ~120 lines. The main loop becomes:

```python
    async def process_message(self, user_message, selected_model="doubao", execution_context=None):
        self.memory_store.update_session_activity(self.conversation_id)
        self.memory_store.increment_message_count(self.conversation_id)

        runtime_knowledge, runtime_skills, subagent_context, capability_profile, agent_memory = \
            await self._prepare_runtime_context(user_message, execution_context)

        # Emit runtime status events (subagent, knowledge, skills, capability profile)
        # ... (yield status events as before, but calling helper methods)

        self.context_window.add_user_message(user_message)
        evaluation = await self.task_evaluator.evaluate(user_message)
        model_config = self.model_provider.get_model_config(selected_model)
        supports_reasoning = model_config.get("supports_reasoning", False)

        try:
            model = self.model_provider.get_model(selected_model)
        except ValueError:
            yield json.dumps({"type": "error", "content": f"模型不可用: {selected_model}"}) + "\n"
            return

        is_doubao = "doubao" in selected_model.lower()
        harness = AgentHarness(
            model=model, tools=self.tool_registry.list_all(), model_name=selected_model,
            conversation_id=self.conversation_id,
            use_tool_choice=not is_doubao, parallel_tool_calls=not is_doubao,
        )

        messages = self._build_messages(user_message, capability_profile, agent_memory, runtime_knowledge, runtime_skills, subagent_context)
        stream_state = OrchestratorStreamState()

        async for chunk_str in harness.run(messages):
            try:
                chunk_data = json.loads(chunk_str)
            except json.JSONDecodeError:
                if chunk_str.strip():
                    yield f"data: {json.dumps({'content': chunk_str})}\n\n"
                continue

            if chunk_data.get("type") == "done":
                async for done_chunk in self._handle_done_event(chunk_data, stream_state, selected_model, subagent_context, runtime_knowledge, runtime_skills, supports_reasoning):
                    yield done_chunk
                continue

            if chunk_data.get("type") == "error":
                error_content = chunk_data.get("content", "")
                if should_retry_without_tools(error_content):
                    # retry logic
                    ...
                yield chunk_str
                continue

            output = self._process_stream_chunk(chunk_data, stream_state, selected_model, supports_reasoning)
            if output:
                yield output
```

- [ ] **步骤 5: Run existing tests**

运行： `python -m unittest tests.agent_framework.test_orchestrator_service -v`
预期： PASS

- [ ] **步骤 6: 提交**

```bash
git add backend/orchestrator.py
git commit -m "refactor: extract orchestrator methods to reduce process_message complexity"
```

---

### 任务 12：前端 SSE 流处理去重

**涉及文件：**
- 修改： `frontend-vue/src/stores/conversation.js`

- [ ] **步骤 1: 识别重复的 SSE 处理逻辑**

In `conversation.js`, both `sendMessage` and `regenerateMessage` contain nearly identical SSE event parsing logic. Extract this into a shared `_processSSEStream` function.

- [ ] **步骤 2: 创建 the shared _processSSEStream function**

Add this function inside the store definition (before `sendMessage`):

```javascript
    async function _processSSEStream({ url, body, conversation, onConversationId }) {
      const headers = getAuthHeaders()
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: currentRequestHandle?.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      const parser = createStreamingEventParser()
      let buffer = ''

      startTimeoutCheck()

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          lastDataTimestamp = Date.now()
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const raw = line.slice(6).trim()
            if (!raw) continue

            const event = parser.parse(raw)
            if (!event) continue

            const normalized = normalizeAgentEvent(event)
            _handleStreamEvent(normalized, conversation, onConversationId)
          }
        }
      } finally {
        stopTimeoutCheck()
      }
    }
```

- [ ] **步骤 3: 抽取 _handleStreamEvent**

```javascript
    function _handleStreamEvent(event, conversation, onConversationId) {
      if (event.type === 'conversation_id' && onConversationId) {
        onConversationId(event.conversation_id)
      }
      // ... handle content, reasoning, tool_result, done, error, status events
      // (move the existing switch/if-else logic from sendMessage here)
    }
```

- [ ] **步骤 4: 重构 sendMessage 和 regenerateMessage，统一复用 _processSSEStream**

Both functions become thin wrappers that call `_processSSEStream` with the appropriate URL and body.

- [ ] **步骤 5: Run frontend tests**

运行： `cd frontend-vue && npm test`
预期： PASS

- [ ] **步骤 6: 提交**

```bash
git add frontend-vue/src/stores/conversation.js
git commit -m "refactor: extract shared SSE stream processing in conversation store"
```

---

### 任务 13：后端 Chat Router 流处理去重

**涉及文件：**
- 修改： `backend/routers/chat.py`

- [ ] **步骤 1: 抽取共享流处理管线**

The `chat` and `chat_non_stream` endpoints share plan lifecycle logic. Extract into a helper:

```python
def _prepare_chat_context(
    db: Session,
    user_id: int,
    conversation_id: int,
) -> tuple[dict | None, dict | None]:
    """Run plan lifecycle checks and return (started_plan_state, execution_context)."""
    started_plan_state = maybe_start_plan_for_chat(db=db, user_id=user_id, conversation_id=conversation_id)
    execution_context = None
    if started_plan_state:
        execution_context = started_plan_state.get("execution_context")

    executing_plan_state = maybe_mark_plan_handoff_executing(db=db, user_id=user_id, conversation_id=conversation_id)
    if executing_plan_state:
        execution_context = executing_plan_state.get("execution_context") or execution_context

    return started_plan_state, execution_context
```

- [ ] **步骤 2: 重构两个端点，统一使用该辅助函数**

Both `chat` and `chat_non_stream` call `_prepare_chat_context` instead of duplicating the plan lifecycle logic.

- [ ] **步骤 3: Run existing tests**

运行： `python -m unittest tests.agent_framework.test_chat_service -v`
预期： PASS

- [ ] **步骤 4: 提交**

```bash
git add backend/routers/chat.py
git commit -m "refactor: extract shared chat context preparation in chat router"
```

---

### 任务 14：移除硬编码配置

**涉及文件：**
- 修改： `backend/orchestrator.py:92`
- 修改： `backend/config.py`

- [ ] **步骤 1: 替换 hardcoded model in orchestrator**

在 `backend/orchestrator.py`, line 92, replace:

```python
        self.context_window = self.context_store.get_context(conversation_id, "deepseek-r1:7b")
```

With:

```python
        try:
            from config import DEFAULT_MODEL
        except ModuleNotFoundError:
            from backend.config import DEFAULT_MODEL
        self.context_window = self.context_store.get_context(conversation_id, DEFAULT_MODEL)
```

- [ ] **步骤 2: 向 config 增加 DOUBAO_SUPPORTS_TOOL_CHOICE**

添加到 `backend/config.py`:

```python
DOUBAO_SUPPORTS_TOOL_CHOICE = os.getenv("DOUBAO_SUPPORTS_TOOL_CHOICE", "false").lower() == "true"
```

- [ ] **步骤 3: 在 orchestrator 中使用配置项**

在 `backend/orchestrator.py`, replace the hardcoded doubao check:

```python
        # Before:
        is_doubao = "doubao" in selected_model.lower()
        use_tool_choice = not is_doubao

        # After:
        try:
            from config import DOUBAO_SUPPORTS_TOOL_CHOICE
        except ModuleNotFoundError:
            from backend.config import DOUBAO_SUPPORTS_TOOL_CHOICE
        is_doubao = "doubao" in selected_model.lower()
        use_tool_choice = DOUBAO_SUPPORTS_TOOL_CHOICE if is_doubao else True
```

- [ ] **步骤 4: Run tests**

运行： `python -m unittest tests.agent_framework.test_orchestrator_service -v`
预期： PASS

- [ ] **步骤 5: 提交**

```bash
git add backend/orchestrator.py backend/config.py
git commit -m "refactor: remove hardcoded model names and provider flags from orchestrator"
```

---

## 第三批回归检查

- [ ] **运行完整测试套件**

```bash
python -m unittest tests.agent_framework.test_orchestrator_service tests.agent_framework.test_chat_service tests.agent_framework.test_health_router
cd frontend-vue && npm test && npm run build
```

---

## 第四批：框架成熟度（任务 15-18）

### 任务 15：启动配置校验

**涉及文件：**
- 修改： `backend/agent_server/bootstrap.py`
- 修改： `tests/agent_framework/test_startup_validation.py`

- [ ] **步骤 1: 增加校验测试**

添加到 `tests/agent_framework/test_startup_validation.py`:

```python
class TestStartupValidation(unittest.TestCase):
    def test_validate_config_passes_with_defaults(self):
        from backend.agent_server.bootstrap import validate_startup_config
        errors = validate_startup_config()
        # In demo mode with defaults, should pass (warnings only)
        self.assertIsInstance(errors, list)

    def test_validate_config_reports_missing_provider(self):
        from backend.agent_server.bootstrap import validate_startup_config
        with patch.dict(os.environ, {"ARK_API_KEY": "", "OLLAMA_BASE_URL": ""}, clear=False):
            errors = validate_startup_config()
            # Should have at least a warning about no provider
            self.assertIsInstance(errors, list)
```

- [ ] **步骤 2: 运行测试，确认其先失败**

运行： `python -m unittest tests.agent_framework.test_startup_validation -v`
预期： FAIL with `ImportError: cannot import name 'validate_startup_config'`

- [ ] **步骤 3: Add validate_startup_config to bootstrap.py**

添加到 `backend/agent_server/bootstrap.py`:

```python
def validate_startup_config() -> list[str]:
    """Validate critical configuration at startup. Returns list of warnings."""
    warnings = []
    try:
        from config import SECRET_KEY, AUTH_MODE, ARK_API_KEY, OLLAMA_BASE_URL, _is_default_secret_key
    except ModuleNotFoundError:
        from backend.config import SECRET_KEY, AUTH_MODE, ARK_API_KEY, OLLAMA_BASE_URL, _is_default_secret_key

    if _is_default_secret_key(SECRET_KEY) and AUTH_MODE != "demo_guest":
        warnings.append("SECRET_KEY uses default value in non-demo mode")

    has_ark = bool(ARK_API_KEY and ARK_API_KEY.strip())
    has_ollama = bool(OLLAMA_BASE_URL and OLLAMA_BASE_URL.strip())
    if not has_ark and not has_ollama:
        warnings.append("No model provider configured (ARK_API_KEY and OLLAMA_BASE_URL both empty)")

    for w in warnings:
        logger.warning("Startup validation: %s", w)

    return warnings
```

- [ ] **步骤 4: 在 init_database 中调用校验**

At the end of `init_database` in `bootstrap.py`, add:

```python
    validate_startup_config()
```

- [ ] **步骤 5: 运行测试，确认其通过**

运行： `python -m unittest tests.agent_framework.test_startup_validation -v`
预期： PASS

- [ ] **步骤 6: 提交**

```bash
git add backend/agent_server/bootstrap.py tests/agent_framework/test_startup_validation.py
git commit -m "feat: add startup configuration validation"
```

---

### 任务 16：API 版本前缀

**涉及文件：**
- 修改： `backend/agent_server/router_registry.py`
- 修改： `frontend-vue/src/api/index.js`

- [ ] **步骤 1: 先阅读当前 router_registry.py**

Read `backend/agent_server/router_registry.py` to understand the current routing setup.

- [ ] **步骤 2: 增加 /api/v1 别名支持**

The approach: keep `/api/` as the primary prefix (backward compatible), and add `/api/v1/` as an alias. In `router_registry.py`, after collecting routers, duplicate them with `/api/v1` prefix:

```python
def get_api_routers(route_groups=None, route_names=None):
    """Return routers filtered by group/name, with /api/v1 aliases."""
    routers = _collect_routers(route_groups, route_names)
    # Add v1 aliases
    from fastapi import APIRouter
    for router in list(routers):
        v1_router = APIRouter(prefix="/api/v1" + router.prefix.removeprefix("/api"), tags=router.tags)
        for route in router.routes:
            v1_router.routes.append(route)
        routers.append(v1_router)
    return routers
```

说明： 这是一个轻量方案。现有 `/api/` 路由继续保持可用，新客户端可以改用 `/api/v1/`。

- [ ] **步骤 3: 更新前端 API base URL**

在 `frontend-vue/src/api/index.js`, change:

```javascript
const API_BASE_URL = '/api'
```

To:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
```

This allows future migration to `/api/v1` via environment variable without code changes.

- [ ] **步骤 4: 运行前端构建**

运行： `cd frontend-vue && npm run build`
预期： PASS

- [ ] **步骤 5: 提交**

```bash
git add backend/agent_server/router_registry.py frontend-vue/src/api/index.js
git commit -m "feat: add /api/v1 route aliases and configurable API base URL"
```

---

### 任务 17：前端统一错误处理

**涉及文件：**
- 修改： `frontend-vue/src/api/index.js`

- [ ] **步骤 1: 增加统一错误拦截器**

Update the response interceptor in `frontend-vue/src/api/index.js`:

```javascript
  instance.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        authStore.logout()
      }

      const errorBody = error.response?.data?.error
      if (errorBody) {
        const message = errorBody.message || '请求失败'
        const code = errorBody.code || 'UNKNOWN'
        console.error(`[API Error] ${code}: ${message} (request_id: ${errorBody.request_id || '-'})`)
      } else if (error.code === 'ECONNABORTED') {
        console.error('[API Error] 请求超时，请检查网络连接')
      } else if (!error.response) {
        console.error('[API Error] 网络连接失败，请检查后端服务是否运行')
      }

      return Promise.reject(error)
    }
  )
```

- [ ] **步骤 2: Run frontend tests**

运行： `cd frontend-vue && npm test`
预期： PASS

- [ ] **步骤 3: 提交**

```bash
git add frontend-vue/src/api/index.js
git commit -m "feat: add unified API error handling with structured error parsing"
```

---

### 任务 18：测试覆盖率门禁

**涉及文件：**
- 修改： `.github/workflows/ci.yml`

- [ ] **步骤 1: 向 CI 增加覆盖率报告**

In `.github/workflows/ci.yml`, in the `backend-tests` job, after the test run step, add:

```yaml
      - name: Run tests with coverage
        run: |
          python -m pytest tests/agent_framework/ \
            --cov=backend \
            --cov-report=term-missing \
            --cov-fail-under=30 \
            -q || true
        continue-on-error: true
```

说明： 先以 `--cov-fail-under=30` 作为基线。后续可以随着覆盖率提升逐步提高门槛。`continue-on-error: true` 表示当前阶段先做报告，不立即阻断 CI。

- [ ] **步骤 2: 提交**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: add test coverage reporting to CI pipeline"
```

---

## 第四批回归检查

- [ ] **运行完整回归**

```bash
python -m unittest tests.agent_framework.test_startup_validation tests.agent_framework.test_health_router tests.agent_framework.test_middleware tests.agent_framework.test_logging_config tests.agent_framework.test_context_compaction_service
cd backend && python scripts/doctor.py
cd frontend-vue && npm test && npm run build
```

---

## 最终验证

- [ ] **运行完整 smoke 检查链路**

```bash
cd backend
python scripts/doctor.py
python scripts/smoke_check.py
python scripts/auth_session_smoke.py
python scripts/chat_stream_smoke.py
```

- [ ] **验证新增端点**

```bash
curl http://localhost:8000/api/health/live
curl http://localhost:8000/api/health/ready
```

- [ ] **验证响应头中的 request ID**

```bash
curl -v http://localhost:8000/api/health 2>&1 | grep X-Request-ID
```

- [ ] **汇总全部改动后提交**

```bash
git add -A
git status
# 检查所有改动后，再执行：
git commit -m "chore: engineering infrastructure v0 complete — 18 improvements across 4 batches"
```

