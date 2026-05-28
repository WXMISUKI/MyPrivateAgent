import os
import json
from pathlib import Path
from dotenv import load_dotenv


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_project_root() -> Path:
    """Resolve the project root directory.

    Supports three scenarios:
    - PROJECT_ROOT env var is set (e.g. in Dockerfile): use it directly
    - Running from project root (local dev): parent.parent has a 'backend' dir
    - Running inside Docker container where backend/ was copied to /app: use parent
    """
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "backend").is_dir():
        return candidate
    return Path(__file__).resolve().parent


PROJECT_ROOT = _resolve_project_root()
IS_VERCEL = os.getenv("VERCEL", "").strip() == "1"

# 加载环境变量
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

# 存储 / 数据库配置
_default_db_mode = "memory" if IS_VERCEL else "sqlite"
DB_MODE = os.getenv("DB_MODE", _default_db_mode).strip().lower() or _default_db_mode
_default_local_data_dir = "/tmp/myprivateagent" if IS_VERCEL else str(PROJECT_ROOT / ".myagent")
LOCAL_DATA_DIR = Path(os.getenv("LOCAL_DATA_DIR", _default_local_data_dir)).resolve()
SQLITE_PATH = Path(os.getenv("SQLITE_PATH", str(LOCAL_DATA_DIR / "app.db"))).resolve()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "MyPrivateAgent")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")

if DB_MODE == "mysql":
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_MODE == "memory":
    DATABASE_URL = "sqlite://"
else:
    DATABASE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
AUTH_MODE = os.getenv("AUTH_MODE", "demo_guest").strip().lower() or "demo_guest"

# Ollama 配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "doubao")

# 豆包模型配置（火山引擎）
ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_MODEL = os.getenv("ARK_MODEL", "doubao-seed-2-0-mini-260215")
ARK_MODEL_ALIAS = os.getenv("ARK_MODEL_ALIAS", "doubao")
ARK_MODEL_DISPLAY_NAME = os.getenv("ARK_MODEL_DISPLAY_NAME", "豆包 (火山引擎)")
ARK_EXTRA_MODELS = os.getenv("ARK_EXTRA_MODELS", "")

# 推理显示配置
SHOW_REASONING = os.getenv("SHOW_REASONING", "false").lower() == "true"
MODEL_CATALOG_JSON = os.getenv("MODEL_CATALOG_JSON", "").strip()


def load_model_catalog_config() -> list[dict]:
    """加载可选的模型目录配置。"""
    if not MODEL_CATALOG_JSON:
        return []
    try:
        parsed = json.loads(MODEL_CATALOG_JSON)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


_DEFAULT_SECRET_KEYS = frozenset({
    "your-secret-key-change-in-production-2026",
    "your-secret-key",
    "changeme",
    "secret",
})


def _is_default_secret_key(key: str) -> bool:
    return key.strip() in _DEFAULT_SECRET_KEYS


def _normalize_origin(origin: str) -> str:
    value = origin.strip().strip('"').strip("'")
    return value.rstrip("/")


CORS_ALLOWED_ORIGINS: list[str] = [
    _normalize_origin(origin)
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:8000",
    ).split(",")
    if _normalize_origin(origin)
]
CORS_ALLOWED_ORIGIN_REGEX = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", "").strip().strip('"').strip("'") or None

RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "20/minute")
DOUBAO_SUPPORTS_TOOL_CHOICE = os.getenv("DOUBAO_SUPPORTS_TOOL_CHOICE", "false").lower() == "true"
SCHEDULER_RUNTIME_BACKEND = os.getenv("SCHEDULER_RUNTIME_BACKEND", "metadata").strip().lower() or "metadata"
_default_embedded_workspace_store_mode = "memory_only" if DB_MODE == "memory" else "strict_sql"
EMBEDDED_WORKSPACE_STORE_MODE = (
    os.getenv("EMBEDDED_WORKSPACE_STORE_MODE", _default_embedded_workspace_store_mode).strip().lower()
    or _default_embedded_workspace_store_mode
)
_default_worker_ownership_store_mode = "memory_only"
WORKER_OWNERSHIP_STORE_MODE = (
    os.getenv("WORKER_OWNERSHIP_STORE_MODE", _default_worker_ownership_store_mode).strip().lower()
    or _default_worker_ownership_store_mode
)
ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER = _env_flag("ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", "false")
ENABLE_LANGGRAPH_DRAFT_ADAPTER = _env_flag("ENABLE_LANGGRAPH_DRAFT_ADAPTER", "false")
ENABLE_LANGGRAPH_RUNTIME_EXECUTION = _env_flag("ENABLE_LANGGRAPH_RUNTIME_EXECUTION", "false")
ENABLE_LANGGRAPH_EXTERNAL_PILOT = _env_flag("ENABLE_LANGGRAPH_EXTERNAL_PILOT", "false")
LANGGRAPH_RUNTIME_ENDPOINT = os.getenv("LANGGRAPH_RUNTIME_ENDPOINT", "").strip()
LANGGRAPH_ASSISTANT_ID = os.getenv("LANGGRAPH_ASSISTANT_ID", "").strip()

# Legacy local voice runtime configuration. Prefer the external unifiedTTSandASR
# capability provider for normal development and production.
ENABLE_VOICE_RUNTIME = _env_flag("ENABLE_VOICE_RUNTIME", "false")
VOICE_ASR_PROVIDER = os.getenv("VOICE_ASR_PROVIDER", "vosk_server").strip() or "vosk_server"
VOICE_TTS_PROVIDER = os.getenv("VOICE_TTS_PROVIDER", "edge_tts").strip() or "edge_tts"
VOSK_MODE = os.getenv("VOSK_MODE", "server").strip() or "server"
VOSK_SERVER_URL = os.getenv("VOSK_SERVER_URL", "ws://127.0.0.1:2700").strip()
VOSK_LANGUAGE = os.getenv("VOSK_LANGUAGE", "zh-cn").strip() or "zh-cn"
VOSK_SAMPLE_RATE = int(os.getenv("VOSK_SAMPLE_RATE", "16000"))
EDGE_TTS_DEFAULT_VOICE = os.getenv("EDGE_TTS_DEFAULT_VOICE", "zh-CN-XiaoxiaoNeural").strip() or "zh-CN-XiaoxiaoNeural"
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%").strip() or "+0%"
EDGE_TTS_VOLUME = os.getenv("EDGE_TTS_VOLUME", "+0%").strip() or "+0%"
EDGE_TTS_PITCH = os.getenv("EDGE_TTS_PITCH", "+0Hz").strip() or "+0Hz"

# External capability provider configuration.
ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER = _env_flag("ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER", "false")
VOICE_CAPABILITY_PROVIDER_BASE_URL = os.getenv("VOICE_CAPABILITY_PROVIDER_BASE_URL", "http://127.0.0.1:8010").strip()
VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS = float(os.getenv("VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS", "5"))
ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER = _env_flag("ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER", "false")
KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL = os.getenv("KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL", "").strip()
KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS = float(os.getenv("KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS", "5"))
