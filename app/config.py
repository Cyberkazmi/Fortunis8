import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN: str | None = None
    OPENAI_API_KEY: str | None = None
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    APP_ENV: str = "development"

    @classmethod
    def reload(cls, env: dict[str, str] | None = None) -> "Settings":
        current_env = env if env is not None else os.environ
        cls.TELEGRAM_BOT_TOKEN = current_env.get("TELEGRAM_BOT_TOKEN")
        cls.OPENAI_API_KEY = current_env.get("OPENAI_API_KEY")
        cls.SUPABASE_URL = current_env.get("SUPABASE_URL")
        cls.SUPABASE_KEY = current_env.get("SUPABASE_KEY")
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


settings = Settings()
settings.reload()


def reload_settings(env: dict[str, str] | None = None) -> Settings:
    return Settings.reload(env)
