from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

GOAL, BELIEF_MODE, RHYTHM = range(3)


@dataclass
class TestProfile:
    user_id: int
    goal: str
    belief_mode: str
    rhythm_minutes: int
    first_ritual: str


@dataclass
class InMemoryTestProfileRepository:
    profiles: dict[int, TestProfile] = field(default_factory=dict)

    def save(self, profile: TestProfile) -> TestProfile:
        self.profiles[profile.user_id] = profile
        return profile

    def get(self, user_id: int) -> TestProfile | None:
        return self.profiles.get(user_id)


GOALS = {
    "study_exams": "Study & exams",
    "business_wealth": "Business & wealth",
    "stress_calm": "Stress & calm",
}
BELIEF_MODES = {
    "scientific": "Scientific",
    "mindfulness": "Mindfulness",
    "religious": "Religious",
    "mixed": "Mixed",
}
RHYTHMS = {"2": 2, "5": 5, "10": 10}


def _buttons(prefix: str, options: dict[str, Any]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=f"test:{prefix}:{key}")] for key, label in options.items()]
    )


def _draft(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    return context.user_data.setdefault("local_test_draft", {})


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["local_test_draft"] = {}
    await update.message.reply_text(
        "Fortunis8 local test bot\n\nChoose one goal to shape your first daily ritual.",
        reply_markup=_buttons("goal", GOALS),
    )
    return GOAL


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, step, value = (query.data or "test:cancel:cancel").split(":", 2)
    draft = _draft(context)

    if step == "goal":
        draft["goal"] = value
        await query.edit_message_text(
            f"Goal selected: {GOALS[value]}\n\nChoose the guidance frame you want. Fortunis8 never infers beliefs.",
            reply_markup=_buttons("belief", BELIEF_MODES),
        )
        return BELIEF_MODE
    if step == "belief":
        draft["belief_mode"] = value
        await query.edit_message_text(
            "Belief mode selected. Choose a realistic daily rhythm:",
            reply_markup=_buttons("rhythm", {key: f"{minutes} minutes" for key, minutes in RHYTHMS.items()}),
        )
        return RHYTHM
    if step == "rhythm":
        minutes = RHYTHMS[value]
        draft["rhythm_minutes"] = minutes
        user_id = update.effective_user.id
        profile_store: InMemoryTestProfileRepository = context.bot_data["profile_store"]
        profile_store.save(
            TestProfile(
                user_id=user_id,
                goal=draft["goal"],
                belief_mode=draft["belief_mode"],
                rhythm_minutes=minutes,
                first_ritual="Take one small action toward your chosen goal.",
            )
        )
        await query.edit_message_text(
            "Your first ritual is ready:\n\n"
            "Take one small action toward your chosen goal.\n\n"
            "This local test uses memory only; no live users, database, notifications, or webhook are connected."
        )
        return ConversationHandler.END
    return ConversationHandler.END


def build_test_application(token: str | None = None, profile_store: InMemoryTestProfileRepository | None = None):
    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError(
            "Missing required environment variable: TELEGRAM_BOT_TOKEN. "
            "Set a test bot token before running the local test bot."
        )
    application = ApplicationBuilder().token(bot_token).build()
    application.bot_data["profile_store"] = profile_store or InMemoryTestProfileRepository()
    flow = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GOAL: [CallbackQueryHandler(callback, pattern=r"^test:goal:")],
            BELIEF_MODE: [CallbackQueryHandler(callback, pattern=r"^test:belief:")],
            RHYTHM: [CallbackQueryHandler(callback, pattern=r"^test:rhythm:")],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    application.add_handler(flow)
    return application


def run_test_bot() -> None:
    # Polling is intentional for this local test harness; no webhook is configured.
    build_test_application().run_polling()


if __name__ == "__main__":
    run_test_bot()
