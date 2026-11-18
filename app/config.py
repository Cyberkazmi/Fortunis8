import os
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN: str | None = None
    OPENAI_API_KEY: str | None = None
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_SECRET_KEY: str | None = None
    PREMIUM_PALM_PRICE_STARS: int = 25
    APP_ENV: str = "development"

    @classmethod
    def reload(cls, env: dict[str, str] | None = None) -> "Settings":
        current_env = env if env is not None else os.environ
        cls.TELEGRAM_BOT_TOKEN = current_env.get("TELEGRAM_BOT_TOKEN")
        cls.OPENAI_API_KEY = current_env.get("OPENAI_API_KEY")
        cls.SUPABASE_URL = current_env.get("SUPABASE_URL")
        explicit_secret = current_env.get("SUPABASE_SECRET_KEY")
        cls.SUPABASE_KEY = current_env.get("SUPABASE_KEY") or explicit_secret
        legacy_key = current_env.get("SUPABASE_KEY", "")
        cls.SUPABASE_SECRET_KEY = explicit_secret or (
            legacy_key if legacy_key.startswith("sb_secret_") else None
        )
        try:
            cls.PREMIUM_PALM_PRICE_STARS = int(
                current_env.get("PREMIUM_PALM_PRICE_STARS", "25")
            )
        except ValueError:
            raise RuntimeError("PREMIUM_PALM_PRICE_STARS must be a positive integer.") from None
        cls.APP_ENV = current_env.get("APP_ENV", "development")
        return cls

    @classmethod
    def validate(cls) -> bool:
        cls.reload()
        if not cls.TELEGRAM_BOT_TOKEN:
            raise RuntimeError(
                "Missing required environment variable: TELEGRAM_BOT_TOKEN. "
                "Set it before starting the Fortunis8 bot."
            )
        if cls.APP_ENV not in {"development", "staging", "production"}:
            raise RuntimeError(
                "APP_ENV must be one of: development, staging, production."
            )
        return True

    @classmethod
    def validate_ai(cls) -> bool:
        cls.reload()
        if not cls.OPENAI_API_KEY:
            raise RuntimeError(
                "Missing required environment variable: OPENAI_API_KEY. "
                "Set it before using AI-generated fortunes."
            )
        return True

    @classmethod
    def validate_supabase(cls) -> bool:
        cls.reload()
        missing = [
            name for name, value in {
                "SUPABASE_URL": cls.SUPABASE_URL,
                "SUPABASE_KEY": cls.SUPABASE_KEY,
            }.items() if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required environment variables for Supabase: "
                + ", ".join(missing)
                + ". Set them before using Supabase-backed profile storage."
            )
        if not cls.SUPABASE_URL.startswith(("http://", "https://")):
            raise RuntimeError("SUPABASE_URL must be a valid HTTP/HTTPS URL.")
        return True

    @classmethod
    def validate_fortunis8(cls) -> bool:
        """Validate the private bot's Telegram and elevated server credentials."""
        cls.reload()
        missing = [
            name for name, value in (
                ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
                ("SUPABASE_URL", cls.SUPABASE_URL),
                ("SUPABASE_SECRET_KEY", cls.SUPABASE_SECRET_KEY),
            ) if not value
        ]
        if missing:
            raise RuntimeError("Missing required Fortunis8 settings: " + ", ".join(missing))
        parsed = urlparse(cls.SUPABASE_URL or "")
        local_http = parsed.hostname in {"localhost", "127.0.0.1"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and local_http):
            raise RuntimeError("SUPABASE_URL must use HTTPS (except local development).")
        if not parsed.netloc or parsed.query or parsed.fragment:
            raise RuntimeError("SUPABASE_URL must be a project base URL without query or fragment.")
        if not (cls.SUPABASE_SECRET_KEY or "").startswith("sb_secret_"):
            raise RuntimeError("SUPABASE_SECRET_KEY must be a Supabase secret key beginning with sb_secret_.")
        if not 1 <= cls.PREMIUM_PALM_PRICE_STARS <= 1000:
            raise RuntimeError("PREMIUM_PALM_PRICE_STARS must be between 1 and 1000.")
        if cls.APP_ENV not in {"development", "staging", "production"}:
            raise RuntimeError("APP_ENV must be one of: development, staging, production.")
        return True


settings = Settings()
settings.reload()


def reload_settings(env: dict[str, str] | None = None) -> Settings:
    return Settings.reload(env)
