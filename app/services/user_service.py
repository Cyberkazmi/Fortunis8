from __future__ import annotations

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.services.fortune_service import (
    ensure_profile,
    generate_horoscope,
    generate_tarot_reading,
    get_mood_options,
    get_persona_options,
    normalize_mood,
    normalize_persona,
    update_profile,
)

PERSONA_SELECTION = 1
MOOD_SELECTION = 2


def _default_reply(user) -> str:
    return (
        "I can guide you with your fortune, tarot, moods, persona, and quest path.\n\n"
        "Try natural messages like:\n"
        "- tell me my fortune\n"
        "- I feel overwhelmed\n"
        "- draw tarot\n"
        "- show my profile\n"
        "- I want to become a Moon Reader"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    persona = profile.get("selected_persona") or "Oracle of Light"
    mood = profile.get("current_mood") or "balanced"

    greeting = (
        "Welcome to Fortunis8 ✨\n\n"
        f"Your guide is: {persona}\n"
        f"Your current mood: {mood}\n\n"
        "You can speak naturally to the bot, or use:\n"
        "/personalize - choose your persona and mood\n"
        "/fortune - get a horoscope\n"
        "/tarot - draw a tarot reading\n"
        "/profile - view your profile\n"
        "/quests - see your current quests"
    )
    await update.message.reply_text(greeting)


async def personalize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    persona_list = ", ".join(get_persona_options())
    await update.message.reply_text(
        "Choose your mystic persona:\n\n"
        f"{persona_list}"
    )
    return PERSONA_SELECTION


async def handle_persona_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    choice = normalize_persona(update.message.text)

    if choice not in get_persona_options():
        await update.message.reply_text(
            "That is not a valid persona. Choose one of:\n\n"
            + ", ".join(get_persona_options())
        )
        return PERSONA_SELECTION

    context.user_data["selected_persona"] = choice
    mood_list = ", ".join(get_mood_options())
    await update.message.reply_text(
        "Excellent. Now tell me how you feel today:\n\n"
        f"{mood_list}"
    )
    return MOOD_SELECTION


async def handle_mood_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    mood = normalize_mood(update.message.text)

    if mood not in get_mood_options():
        await update.message.reply_text(
            "That mood is not recognized. Choose one of:\n\n"
            + ", ".join(get_mood_options())
        )
        return MOOD_SELECTION

    context.user_data["current_mood"] = mood
    profile = ensure_profile(user)
    updated = update_profile(
        user,
        selected_persona=context.user_data.get("selected_persona", profile.get("selected_persona", "Oracle of Light")),
        current_mood=mood,
    )

    persona = updated.get("selected_persona") or profile.get("selected_persona") or "Oracle of Light"
    reading = generate_horoscope(
        profile.get("zodiac_sign") or "aries",
        user_name=(user.first_name or "Seeker"),
        mood=mood,
        persona=persona,
    )

    await update.message.reply_text(
        f"Your mystical identity is now set.\n\n"
        f"Persona: {persona}\n"
        f"Mood: {mood}\n\n"
        "Your first aligned reading is ready:\n\n"
        f"{reading}"
    )
    return ConversationHandler.END


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    sign = profile.get("zodiac_sign") or "aries"
    mood = profile.get("current_mood") or "balanced"
    persona = profile.get("selected_persona") or "Oracle of Light"
    reading = generate_horoscope(sign, user_name=(user.first_name or "Seeker"), mood=mood, persona=persona)
    await update.message.reply_text(reading)


async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    question = "What should I focus on today?"
    mood = profile.get("current_mood") or "balanced"
    persona = profile.get("selected_persona") or "Oracle of Light"
    reading = generate_tarot_reading(
        question,
        user_name=(user.first_name or "Seeker"),
        mood=mood,
        persona=persona,
    )
    await update.message.reply_text(reading)


async def horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    sign = context.args[0].lower() if context.args else (profile.get("zodiac_sign") or "aries")
    mood = profile.get("current_mood") or "balanced"
    persona = profile.get("selected_persona") or "Oracle of Light"
    reading = generate_horoscope(sign, user_name=(user.first_name or "Seeker"), mood=mood, persona=persona)
    await update.message.reply_text(reading)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = ensure_profile(user)
    message = (
        f"User: {user.first_name or 'Seeker'}\n"
        f"Username: @{user.username or 'unknown'}\n"
        f"Persona: {profile.get('selected_persona', 'Oracle of Light')}\n"
        f"Mood: {profile.get('current_mood', 'balanced')}\n"
        f"Zodiac Sign: {profile.get('zodiac_sign') or 'Not set'}\n"
        f"Diamonds: {profile.get('diamonds', 0)}\n"
        f"Level: {profile.get('level', 1)}\n"
        f"Streak: {profile.get('streak_count', 0)}"
    )
    await update.message.reply_text(message)


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return

    user = update.effective_user
    lower_text = text.lower()
    profile = ensure_profile(user)

    if "profile" in lower_text or "status" in lower_text or "how am i doing" in lower_text:
        await profile(update, context)
        return

    if "fortune" in lower_text or "horoscope" in lower_text or "reading for today" in lower_text:
        await fortune(update, context)
        return

    if "tarot" in lower_text or "card" in lower_text:
        await tarot(update, context)
        return

    if "feel" in lower_text or "mood" in lower_text or any(word in lower_text for word in ["stressed", "anxious", "hopeful", "lonely", "balanced", "sad", "ambitious", "curious"]):
        detected_mood = normalize_mood(text)
        update_profile(user, current_mood=detected_mood)
        await update.message.reply_text(
            f"I’ve noted your mood as: {detected_mood}.\n\n"
            "Your readings will now align with how you are feeling."
        )
        return

    if any(word in lower_text for word in ["oracle", "sun warrior", "moon reader", "guardian", "shadow"]):
        detected_persona = normalize_persona(text)
        update_profile(user, selected_persona=detected_persona)
        await update.message.reply_text(
            f"Your persona is now set to: {detected_persona}.\n\n"
            "Your future readings will reflect this guide."
        )
        return

    await update.message.reply_text(_default_reply(user))


def build_application():
    settings.validate()
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    personalization = ConversationHandler(
        entry_points=[CommandHandler("personalize", personalize)],
        states={
            PERSONA_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_persona_choice)],
            MOOD_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mood_choice)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    application.add_handler(personalization)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fortune", fortune))
    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("horoscope", horoscope))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text))
    return application
