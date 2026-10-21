from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler

from app.config import settings
from app.services.fortune_service import generate_horoscope, generate_tarot_reading
from app.services.streak_service import apply_daily_reward
from app.services.user_service import ensure_profile, update_profile


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)

    reward_result = apply_daily_reward(profile, context.user_data)
    if reward_result["reward_earned"]:
        profile = reward_result["profile"]
        context.user_data["last_daily_date"] = reward_result["new_last_daily_date"]
        update_profile(
            user,
            diamonds=profile.get("diamonds", 0),
            streak_count=profile.get("streak_count", 0),
            level=profile.get("level", 1),
        )
        status_line = reward_result["message"]
    else:
        context.user_data["last_daily_date"] = reward_result["new_last_daily_date"]
        status_line = reward_result["message"]

    greeting = (
        "Welcome to Fortunis8 ✨\n\n"
        f"Your current streak: {profile.get('streak_count', 0)}\n"
        f"Your diamonds: {profile.get('diamonds', 0)}\n"
        f"Your level: {profile.get('level', 1)}\n\n"
        f"{status_line}\n\n"
        "Commands:\n"
        "/start - begin your journey\n"
        "/fortune - get a general fortune\n"
        "/tarot - draw a tarot reading\n"
        "/horoscope <sign> - get a horoscope\n"
        "/profile - view your profile"
    )

    await update.message.reply_text(greeting)


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)

    reward_result = apply_daily_reward(profile, context.user_data)
    if reward_result["reward_earned"]:
        profile = reward_result["profile"]
        context.user_data["last_daily_date"] = reward_result["new_last_daily_date"]
        update_profile(
            user,
            diamonds=profile.get("diamonds", 0),
            streak_count=profile.get("streak_count", 0),
            level=profile.get("level", 1),
        )
        reward_message = reward_result["message"]
    else:
        context.user_data["last_daily_date"] = reward_result["new_last_daily_date"]
        reward_message = reward_result["message"]

    sign = profile.get("zodiac_sign") or "aries"
    reading = generate_horoscope(sign, user_name=(user.first_name or "Seeker"))

    await update.message.reply_text(f"{reward_message}\n\n{reading}")


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
    profile = ensure_profile(user)

    message = (
        f"User: {user.first_name or 'Seeker'}\n"
        f"Username: @{user.username or 'unknown'}\n"
        f"Persona: {profile.get('selected_persona', 'Oracle of Light')}\n"
        f"Zodiac Sign: {profile.get('zodiac_sign') or 'Not set'}\n"
        f"Diamonds: {profile.get('diamonds', 0)}\n"
        f"Level: {profile.get('level', 1)}\n"
        f"Streak: {profile.get('streak_count', 0)}"
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
