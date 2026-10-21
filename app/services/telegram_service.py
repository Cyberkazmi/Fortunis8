from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler

from app.config import settings
from app.services.fortune_service import (
    generate_horoscope,
    generate_tarot_reading,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Fortunis8 ✨\n\n"
        "Commands:\n"
        "/start - begin your journey\n"
        "/fortune - get a general fortune\n"
        "/tarot - draw a tarot reading\n"
        "/horoscope <sign> - get a horoscope\n"
        "/profile - view your profile"
    )


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reading = generate_horoscope("aries", user_name=(update.effective_user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = "What should I focus on today?"
    reading = generate_tarot_reading(question, user_name=(update.effective_user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sign = context.args[0].lower() if context.args else "aries"
    reading = generate_horoscope(sign, user_name=(update.effective_user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = (
        f"User: {user.first_name or 'Seeker'}\n"
        f"Username: @{user.username or 'unknown'}\n"
        "Status: Mystic traveler\n"
        "Diamonds: 0\n"
        "Level: 1"
    )
    await update.message.reply_text(message)


def build_application():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fortune", fortune))
    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("horoscope", horoscope))
    application.add_handler(CommandHandler("profile", profile))
    return application
