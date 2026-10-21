import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    APP_ENV = os.getenv("APP_ENV", "development")

    @classmethod
    def validate(cls) -> bool:
        required = {
            "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
        }

        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing)
                + ". Ensure your .env file is configured before starting the bot."
            )

        if not cls.SUPABASE_URL.startswith(("http://", "https://")):
            raise RuntimeError("SUPABASE_URL must be a valid HTTP/HTTPS URL.")

        if cls.APP_ENV not in {"development", "staging", "production"}:
            raise RuntimeError(
                "APP_ENV must be one of: development, staging, production."
            )

        return True


settings = Settings()
