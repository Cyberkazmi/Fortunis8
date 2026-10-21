from telegram import Update
from telegram.ext import (
    ContextTypes,
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.services.fortune_service import (
    generate_horoscope,
    generate_tarot_reading,
)
from app.services.rewards_service import apply_welcome_reward, award_diamonds_and_level
from app.services.user_service import ensure_profile, update_profile

CHOOSING_SIGN = 1
CHOOSING_PERSONA = 2


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)

    if profile.get("local_mode"):
        greeting = (
            "Welcome to Fortunis8 ✨\n\n"
            "Your local startup profile is ready.\n"
            "Set your Supabase credentials in .env to save user data.\n\n"
            "To begin your journey, send /onboard"
        )
    else:
        greeting = (
            f"Welcome back, {user.first_name or 'Seeker'} ✨\n\n"
            f"Your Fortunis8 profile is ready.\n"
            f"Diamonds: {profile.get('diamonds', 0)}\n"
            f"Level: {profile.get('level', 1)}\n\n"
            "To begin your journey, send /onboard"
        )

    await update.message.reply_text(greeting)


async def onboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_profile(user)

    await update.message.reply_text(
        "Let us prepare your fortune identity.\n\n"
        "Choose your zodiac sign by sending one of these values:\n\n"
        "Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces"
    )
    return CHOOSING_SIGN


async def handle_sign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sign = update.message.text.strip().title()
    valid_signs = {
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    }

    if sign not in valid_signs:
        await update.message.reply_text(
            "That is not a valid zodiac sign. Please choose one from the list:\n\n"
            "Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces"
        )
        return CHOOSING_SIGN

    context.user_data["zodiac_sign"] = sign
    await update.message.reply_text(
        "Great. Now choose your mystical persona:\n\n"
        "Oracle of Light\n"
        "Sun Warrior\n"
        "Moon Reader\n"
        "Guardian of Fortune\n"
        "Shadow Seer"
    )
    return CHOOSING_PERSONA


async def handle_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    persona = update.message.text.strip()
    valid_personas = {
        "Oracle of Light",
        "Sun Warrior",
        "Moon Reader",
        "Guardian of Fortune",
        "Shadow Seer",
    }

    if persona not in valid_personas:
        await update.message.reply_text(
            "That is not a valid persona. Please choose one of these:\n\n"
            "Oracle of Light\n"
            "Sun Warrior\n"
            "Moon Reader\n"
            "Guardian of Fortune\n"
            "Shadow Seer"
        )
        return CHOOSING_PERSONA

    user = update.effective_user
    profile = ensure_profile(user)
    current_balance = profile.get("diamonds", 0)
    new_balance, new_level = award_diamonds_and_level(current_balance, 25)

    context.user_data["selected_persona"] = persona
    update_profile(
        user,
        zodiac_sign=context.user_data.get("zodiac_sign"),
        selected_persona=persona,
        diamonds=new_balance,
        streak_count=profile.get("streak_count", 0) + 1,
        level=new_level,
    )

    fortune = generate_horoscope(
        context.user_data.get("zodiac_sign", "aries"),
        user_name=(user.first_name or "Seeker"),
    )

    await update.message.reply_text(
        f"Your profile is complete, {user.first_name or 'Seeker'} ✨\n\n"
        f"Zodiac Sign: {context.user_data.get('zodiac_sign')}\n"
        f"Persona: {persona}\n"
        f"Welcome reward: +25 diamonds\n"
        f"Current diamonds: {new_balance}\n\n"
        "Your first daily fortune is here:\n\n"
        f"{fortune}"
    )
    return ConversationHandler.END


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sign = context.user_data.get("zodiac_sign", "aries")
    reading = generate_horoscope(sign, user_name=(update.effective_user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = "What should I focus on today?"
    reading = generate_tarot_reading(question, user_name=(update.effective_user.first_name or "Seeker"))
    await update.message.reply_text(reading)


async def horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sign = context.args[0].lower() if context.args else context.user_data.get("zodiac_sign", "aries")
    reading = generate_horoscope(sign, user_name=(update.effective_user.first_name or "Seeker"))
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


def build_application():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    onboarding = ConversationHandler(
        entry_points=[CommandHandler("onboard", onboard)],
        states={
            CHOOSING_SIGN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sign)
            ],
            CHOOSING_PERSONA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_persona)
            ],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    application.add_handler(onboarding)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fortune", fortune))
    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("horoscope", horoscope))
    application.add_handler(CommandHandler("profile", profile))

    return application
