from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from app.services.progression_service import (
    complete_prototype_quest,
    format_progression_summary,
    new_progression,
)

PATH_GOALS, PATH_MODE, PATH_STATE, PATH_RHYTHM, PATH_REVIEW = range(10, 15)
CATALOG_PATH = Path(__file__).resolve().parents[2] / "seeds" / "fortunis8_catalog.json"


def _catalog() -> dict[str, Any]:
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "goals": [["study_exams", "Study & exam preparation", "پڑھائی اور امتحان", ""]],
            "modes": [["scientific", "Scientific", "", "", False]],
            "states": [["motivated", "Motivated", "پرجوش"]],
        }


def _draft(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    return context.user_data.setdefault(
        "path_draft",
        {"goals": [], "guidance_mode": None, "current_state": None, "duration_minutes": 5, "delivery_window": "morning"},
    )


def _goal_label(key: str) -> str:
    return next((row[1] for row in _catalog()["goals"] if row[0] == key), key)


def _mode_label(key: str | None) -> str:
    return next((row[1] for row in _catalog()["modes"] if row[0] == key), key or "Not selected")


def _goals_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for key, label, *_ in _catalog()["goals"]:
        mark = "✓ " if key in selected else ""
        rows.append([InlineKeyboardButton(f"{mark}{label}", callback_data=f"path:goal:{key}")])
    rows.append([InlineKeyboardButton("Continue →", callback_data="path:goals_next")])
    return InlineKeyboardMarkup(rows)


def _modes_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key, label, *_ in _catalog()["modes"]:
        rows.append([InlineKeyboardButton(label, callback_data=f"path:mode:{key}")])
    return InlineKeyboardMarkup(rows)


def _states_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(row[1], callback_data=f"path:state:{row[0]}")] for row in _catalog()["states"]]
        + [[InlineKeyboardButton("Prefer not to say", callback_data="path:state:prefer_not_to_say")]]
    )


def _rhythm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("5 minutes", callback_data="path:duration:5"), InlineKeyboardButton("10 minutes", callback_data="path:duration:10")],
            [InlineKeyboardButton("Morning", callback_data="path:window:morning"), InlineKeyboardButton("Evening", callback_data="path:window:evening")],
        ]
    )


def _summary(draft: dict[str, Any]) -> str:
    goals = ", ".join(_goal_label(key) for key in draft.get("goals", [])) or "None selected"
    return (
        "Your sample path:\n\n"
        f"Goals: {goals}\n"
        f"Guidance: {_mode_label(draft.get('guidance_mode'))}\n"
        f"Starting point: {draft.get('current_state', 'Not selected')}\n"
        f"Rhythm: {draft.get('duration_minutes', 5)} minutes · {draft.get('delivery_window', 'morning')} delivery"
    )


async def path_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["path_draft"] = {"goals": [], "guidance_mode": None, "current_state": None, "duration_minutes": 5, "delivery_window": "morning"}
    await update.message.reply_text(
        "Build your Fortunis8 daily path.\n\n"
        "Choose goals and preferences from buttons; you do not need to write a long profile.\n"
        "This prototype keeps selections in Telegram session memory only.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Start choosing →", callback_data="path:welcome")]]),
    )
    return PATH_REVIEW


async def path_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    value = parts[2] if len(parts) > 2 else ""
    draft = _draft(context)

    if action == "welcome":
        await query.edit_message_text("Step 1 of 6 · Choose one or more goals:", reply_markup=_goals_keyboard(draft["goals"]))
        return PATH_GOALS
    if action == "goal":
        if value in draft["goals"]:
            draft["goals"].remove(value)
        else:
            draft["goals"].append(value)
        await query.edit_message_text(
            "Step 2 of 6 · Choose one or more goals.\n\n"
            f"Selected: {', '.join(_goal_label(key) for key in draft['goals']) or 'None yet'}",
            reply_markup=_goals_keyboard(draft["goals"]),
        )
        return PATH_GOALS
    if action == "goals_next":
        if not draft["goals"]:
            await query.edit_message_text("Choose at least one goal before continuing.", reply_markup=_goals_keyboard(draft["goals"]))
            return PATH_GOALS
        await query.edit_message_text("Step 3 of 6 · Choose the guidance mode you want Fortunis8 to use:", reply_markup=_modes_keyboard())
        return PATH_MODE
    if action == "mode":
        draft["guidance_mode"] = value
        await query.edit_message_text("Step 4 of 6 · Where are you starting from today? This is optional and not a diagnosis.", reply_markup=_states_keyboard())
        return PATH_STATE
    if action == "state":
        draft["current_state"] = value.replace("_", " ")
        await query.edit_message_text("Step 5 of 6 · Choose a realistic daily rhythm:", reply_markup=_rhythm_keyboard())
        return PATH_RHYTHM
    if action == "duration":
        draft["duration_minutes"] = int(value)
        await query.edit_message_text("Choose your delivery window:", reply_markup=_rhythm_keyboard())
        return PATH_RHYTHM
    if action == "window":
        draft["delivery_window"] = value
        await query.edit_message_text("Step 6 of 6 · Review your path:\n\n" + _summary(draft), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirm my path", callback_data="path:confirm"), InlineKeyboardButton("Cancel", callback_data="path:cancel")]]))
        return PATH_REVIEW
    if action == "confirm":
        context.user_data["path_profile"] = dict(draft)
        context.user_data["path_quests"] = new_progression()
        await query.edit_message_text(_summary(draft) + "\n\nYour first quests are ready. Use /quests, then /done daily_ritual to test progression.\n\nPrototype note: authentication, database persistence, and notifications are not connected yet.")
        return ConversationHandler.END
    if action == "cancel":
        context.user_data.pop("path_draft", None)
        await query.edit_message_text("Path setup cancelled. Use /path whenever you want to try it again.")
        return ConversationHandler.END

    return PATH_REVIEW


async def cancel_path(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("path_draft", None)
    await update.message.reply_text("Path setup cancelled. Use /path to start again.")
    return ConversationHandler.END


async def path_quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("path_profile"):
        await update.message.reply_text("Build your daily path first with /path.")
        return
    await update.message.reply_text(format_progression_summary(context.user_data.get("path_quests")))


async def complete_path_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("path_profile"):
        await update.message.reply_text("Build your daily path first with /path.")
        return
    quest_key = context.args[0] if context.args else context.user_data.pop("pending_quest_key", "")
    if not quest_key:
        await path_quests(update, context)
        return
    state, result = complete_prototype_quest(context.user_data.get("path_quests"), quest_key)
    context.user_data["path_quests"] = state
    await update.message.reply_text(result["message"])


def build_path_conversation() -> ConversationHandler:
    callback = CallbackQueryHandler(path_callback, pattern=r"^path:")
    return ConversationHandler(
        entry_points=[CommandHandler("path", path_onboarding), CommandHandler("onboard", path_onboarding)],
        states={PATH_GOALS: [callback], PATH_MODE: [callback], PATH_STATE: [callback], PATH_RHYTHM: [callback], PATH_REVIEW: [callback]},
        fallbacks=[CommandHandler("cancel", cancel_path)],
        allow_reentry=True,
    )
