from app.bot.handlers import build_application


def main() -> None:
    application = build_application()
    print("Fortunis8 bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
