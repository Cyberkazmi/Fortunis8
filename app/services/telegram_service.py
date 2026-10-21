from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.services.fortune_service import generate_horoscope, generate_tarot_reading
from app.services.quest_service import complete_quest, detect_quest_intent, get_quest_summary
from app.services.streak_service import apply_daily_reward
from app.services.user_service import ensure_profile, update_profile


def _default_user_reply(user) -> str:
    return (
        "I can help with your fortune, tarot, streak, quests, and profile.\n\n"
        "Try saying things like:\n"
        "- tell me my fortune\n"
        "- draw tarot\n"
        "- show my quests\n"
        "- how am I doing?"
    )


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
        reward_message = reward_result["message"]
    else:
        context.user_data["last_daily_date"] = reward_result["new_last_daily_date"]
        reward_message = reward_result["message"]

    greeting = (
        "Welcome to Fortunis8 ✨\n\n"
        f"Current streak: {profile.get('streak_count', 0)}\n"
        f"Diamonds: {profile.get('diamonds', 0)}\n"
        f"Level: {profile.get('level', 1)}\n\n"
        f"{reward_message}\n\n"
        "You can talk to me naturally. Try:\n"
        "- tell me my fortune\n"
        "- draw tarot\n"
        "- show my quests\n"
        "- give me my profile"
    )
    await update.message.reply_text(greeting)


async def quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    summary = get_quest_summary(user)
    await update.message.reply_text(summary)


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    sign = profile.get("zodiac_sign") or "aries"
    reading = generate_horoscope(sign, user_name=(user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    question = "What should I focus on today?"
    reading = generate_tarot_reading(question, user_name=(user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    sign = context.args[0].lower() if context.args else (profile.get("zodiac_sign") or "aries")
    reading = generate_horoscope(sign, user_name=(user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)

    message = (
        f"User: {user.first_name or 'Seeker'}\n"
        f"Username: @{user.username or 'unknown'}\n"
        f"Zodiac Sign: {profile.get('zodiac_sign') or 'Not set'}\n"
        f"Persona: {profile.get('selected_persona', 'Oracle of Light')}\n"
        f"Diamonds: {profile.get('diamonds', 0)}\n"
        f"Level: {profile.get('level', 1)}\n"
        f"Streak: {profile.get('streak_count', 0)}"
    )
    await update.message.reply_text(message)


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (update.message.text or "").strip()
    if not text:
        return

    lower_text = text.lower()

    if any(term in lower_text for term in ["quest", "quests", "mission", "show my quests", "my missions"]):
        await quests(update, context)
        return

    if any(term in lower_text for term in ["profile", "stats", "status", "how am i doing"]):
        await profile(update, context)
        return

    if "fortune" in lower_text or "horoscope" in lower_text or "reading for today" in lower_text:
        await fortune(update, context)
        return

    if "tarot" in lower_text or "card" in lower_text:
        await tarot(update, context)
        return

    intent = detect_quest_intent(text)
    if intent:
        result = complete_quest(user, intent)
        if result.get("completed"):
            if intent == "daily_fortune":
                profile = ensure_profile(user)
                sign = profile.get("zodiac_sign") or "aries"
                reading = generate_horoscope(sign, user_name=(user.first_name or "Seeker"))
                await update.message.reply_text(f"{result['message']}\n\n{reading}")
                return

            if intent == "tarot_focus":
                reading = generate_tarot_reading("What should I focus on today?", user_name=(user.first_name or "Seeker"))
                await update.message.reply_text(f"{result['message']}\n\n{reading}")
                return

            await update.message.reply_text(f"{result['message']}\n\nYour path grows brighter with each small act of devotion.")
            return

    await update.message.reply_text(_default_user_reply(user))


def build_application():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fortune", fortune))
    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("horoscope", horoscope))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("quests", quests))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text)
    )

    return application
