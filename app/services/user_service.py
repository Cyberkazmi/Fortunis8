from __future__ import annotations

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
    DEFAULT_MOOD,
    DEFAULT_PERSONA,
    generate_horoscope,
    generate_tarot_reading,
    normalize_mood,
    normalize_persona,
)
from app.services.user_service import (
    ensure_profile,
    get_mood_options,
    get_persona_options,
    start,
    personalize,
    handle_persona_choice,
    handle_mood_choice,
    handle_free_text,
    fortune,
    tarot,
    horoscope,
    profile,
    update_profile,
)

PERSONA_SELECTION = 1
MOOD_SELECTION = 2


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
