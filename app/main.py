from app.bot.handlers import build_application
from app.config import settings


def main() -> None:
    settings.validate()
    application = build_application()
    print("Fortunis8 bot is starting...")
    print(f"Environment: {settings.APP_ENV}")
    application.run_polling()


if __name__ == "__main__":
    main()
