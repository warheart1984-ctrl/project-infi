from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("JARVIS_DATA_DIR", str(BASE_DIR / "data"))).resolve()
CHROMA_DIR = Path(os.getenv("JARVIS_CHROMA_DIR", str(DATA_DIR / "chroma"))).resolve()
DB_PATH = Path(os.getenv("JARVIS_DB_PATH", str(DATA_DIR / "jarvis.db"))).resolve()


def _has_modern_frontend_bundle(directory: Path) -> bool:
    return (directory / "index.html").exists() and (directory / "assets").is_dir()


def _resolve_static_dir() -> Path:
    explicit_static_dir = os.getenv("JARVIS_STATIC_DIR", "").strip()
    if explicit_static_dir:
        return Path(explicit_static_dir).expanduser().resolve()

    packaged_static_dir = BASE_DIR / "app" / "static"
    frontend_build_dir = BASE_DIR / "frontend" / "build"

    if _has_modern_frontend_bundle(packaged_static_dir):
        return packaged_static_dir.resolve()
    if _has_modern_frontend_bundle(frontend_build_dir):
        return frontend_build_dir.resolve()
    return packaged_static_dir.resolve()


STATIC_DIR = _resolve_static_dir()

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MAIN_MODEL = os.getenv("OPENAI_MAIN_MODEL", "gpt-4o-mini")
OPENAI_FAST_MODEL = os.getenv("OPENAI_FAST_MODEL", OPENAI_MAIN_MODEL)
APP_BEARER_TOKEN = os.getenv("APP_BEARER_TOKEN", "").strip()
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "").strip().lower() in {"1", "true", "yes", "on"}
ALLOW_OPERATOR_REGISTRATION = os.getenv("ALLOW_OPERATOR_REGISTRATION", "true").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
APP_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "APP_CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:3100,http://localhost:3100",
    ).split(",")
    if origin.strip()
]
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")

WORKFLOW_LEASE_SECONDS = int(os.getenv("WORKFLOW_LEASE_SECONDS", "45"))
WORKFLOW_HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("WORKFLOW_HEARTBEAT_INTERVAL_SECONDS", "10"))
WORKFLOW_QUEUE_STALE_SECONDS = int(os.getenv("WORKFLOW_QUEUE_STALE_SECONDS", "45"))
WORKFLOW_MAX_RECOVERY_ATTEMPTS = int(os.getenv("WORKFLOW_MAX_RECOVERY_ATTEMPTS", "3"))
WORKFLOW_SWEEPER_LIMIT = int(os.getenv("WORKFLOW_SWEEPER_LIMIT", "25"))
