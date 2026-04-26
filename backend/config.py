import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量 - 确保从项目根目录加载
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 存储 / 数据库配置
DB_MODE = os.getenv("DB_MODE", "sqlite").strip().lower() or "sqlite"
LOCAL_DATA_DIR = Path(os.getenv("LOCAL_DATA_DIR", str(PROJECT_ROOT / ".myagent"))).resolve()
SQLITE_PATH = Path(os.getenv("SQLITE_PATH", str(LOCAL_DATA_DIR / "app.db"))).resolve()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "MyPrivateAgent")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")

if DB_MODE == "mysql":
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Ollama 配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "doubao")

# 豆包模型配置（火山引擎）
ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_MODEL = os.getenv("ARK_MODEL", "doubao-seed-2-0-mini-260215")

# 推理显示配置
SHOW_REASONING = os.getenv("SHOW_REASONING", "false").lower() == "true"

# 可用模型列表
AVAILABLE_MODELS = [
    {
        "name": "doubao",
        "display_name": "豆包 (火山引擎)",
        "type": "cloud",
        "has_reasoning": False,
        "provider": "volcengine"
    },
    {
        "name": "llama3.1",
        "display_name": "Llama 3.1",
        "type": "local",
        "has_reasoning": False,
        "provider": "ollama"
    },
    {
        "name": "deepseek-r1:7b",
        "display_name": "DeepSeek R1 7B",
        "type": "local",
        "has_reasoning": True,
        "provider": "ollama"
    },
    {
        "name": "llava",
        "display_name": "LLaVA",
        "type": "local",
        "has_reasoning": False,
        "provider": "ollama"
    },
]
