"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader so the app works without python-dotenv at import time
    (python-dotenv is still used in run.py for convenience)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "app.db"))
    SENTIMENT_ANALYZER = os.environ.get("SENTIMENT_ANALYZER", "vader")
    NEGATIVE_PCT_ALERT_THRESHOLD = float(os.environ.get("NEGATIVE_PCT_ALERT_THRESHOLD", "40"))
    AVG_RATING_ALERT_THRESHOLD = float(os.environ.get("AVG_RATING_ALERT_THRESHOLD", "2.5"))
    MIN_RESPONSES_FOR_ALERT = int(os.environ.get("MIN_RESPONSES_FOR_ALERT", "3"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours
