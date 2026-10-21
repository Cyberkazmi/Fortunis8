import os
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN: ClassVar[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENAI_API_KEY: ClassVar[str | None] = os.getenv("OPENAI_API_KEY")
    SUPABASE_URL: ClassVar[str | None] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: ClassVar[str | None] = os.getenv("SUPABASE_KEY")
    APP_ENV: ClassVar[str] = os.getenv("APP_ENV", "development")

    @classmethod
    def validate(cls) -> bool:
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
        if not cls.OPENAI_API_KEY:
            raise RuntimeError(
                "Missing required environment variable: OPENAI_API_KEY. "
                "Set it before using AI-generated fortunes."
            )
        return True

    @classmethod
    def validate_supabase(cls) -> bool:
        missing = [
            name
            for name, value in {
                "SUPABASE_URL": cls.SUPABASE_URL,
                "SUPABASE_KEY": cls.SUPABASE_KEY,
            }.items()
            if not value
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
