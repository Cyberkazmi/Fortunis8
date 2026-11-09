"""Bilingual Fortunis8 Telegram flows added beside the repository's original services.

All persistent Fortunis8 actions use the server-only Supabase REST store. The
bot does not persist horoscope birth inputs, process hand photos, or treat points
as cash. Telegram Stars are used only for premium reading entitlements.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    TypeHandler,
    filters,
)

from app.config import settings
from app.db.fortunis8_store import PersistenceError, SupabaseRestUserStore
from app.services.domain import (
    SAFETY_DISCLAIMER,
    charity_quest,
    fortune,
    horoscope_reading,
    menu_translations,
    palm_reading,
    persona_style,
    skill_game,
    supported_personas,
    sun_sign,
    tarot,
)

logger = logging.getLogger(__name__)
TEXT: dict[str, dict[str, str]] = {
    "en": {
        "welcome": "Welcome to Fortunis8. Choose a language, then explore the menu.",
        "language_saved": "Language saved: English.",
        "menu": "Fortunis8 menu — readings and games are for entertainment only.",
        "unavailable": "Fortunis8 is temporarily unavailable. Your request was not marked as complete; please try again later.",
        "private_only": "Please use Fortunis8 in a private Telegram chat.",
        "daily_done": "Today's daily reward was already claimed.",
        "daily_claim": "Daily reward: +{reward} diamonds. Streak: {streak}. Balance: {balance}.",
        "profile": "Diamonds: {diamonds}\nLevel: {level}\nDaily streak: {streak}\nPremium reading credits: {credits}\nPersona: {persona}",
        "no_reading": "No saved reading yet. Choose a reading from the menu.",
        "horoscope_prompt": "Send birth details as `YYYY-MM-DD HH:MM, City` (example: `1995-08-20 09:30, Lahore`). These details are used once to make a playful sun-sign reading and are not saved. This is not a full astronomical kundli.",
        "horoscope_invalid": "That format was not recognized. Send `YYYY-MM-DD HH:MM, City`, for example `1995-08-20 09:30, Lahore`. The details are not saved.",
        "horoscope_future": "Please use a valid past birth date. The details are not saved.",
        "cancelled": "Horoscope entry cancelled.",
        "focus": "Choose a focus. A palm-themed text reflection does not analyze hand photos.",
        "palm_basic_title": "Basic palm-themed reflection",
        "palm_premium_title": "Detailed palm-themed reflection",
        "premium_price": "Choose a focus for one detailed reading ({price} Telegram Stars). Payment is only for this reading; diamonds are not sold.",
        "credits_available": "You have {credits} premium reading credit(s). Choose a focus to use one.",
        "payment_credit": "Payment verified. Your detailed reading is below. Remaining credit(s): {credits}.",
        "premium_update_duplicate": "This Telegram request was already processed. Use /last to view your latest saved reading.",
        "payment_verified_credit_pending": "Payment verified and one reading credit is ready. Open Premium palm reading from the menu to use it.",
        "payment_duplicate": "This Telegram Stars payment was already processed. Use /last to view your latest saved reading.",
        "payment_invalid": "We could not verify this payment with the Fortunis8 database. Do not pay again; ask the bot owner to review the transaction.",
        "payment_unavailable": "Payment verification is temporarily unavailable. Please try again later.",
        "invoice_unavailable": "A Stars invoice could not be created right now. You were not charged.",
        "precheckout_failed": "This Stars invoice is invalid or expired. No payment was taken.",
        "game_choose": "Choose a no-cost skill challenge. Hard mode offers more points for a correct answer; points have no cash value.",
        "game_question": "{difficulty} challenge: {question}",
        "game_correct": "Correct. +{reward} diamonds. Balance: {balance}.",
        "game_wrong": "Not quite. No diamonds were deducted; try another challenge.",
        "game_expired": "This challenge expired. Start a new one from the menu.",
        "game_used": "That challenge was already submitted.",
        "leaderboard": "Anonymous leaderboard (diamonds only):\n{rows}\n\nYour place: {rank}",
        "leaderboard_empty": "The leaderboard is empty so far.",
        "personas": "Choose a persona. The names are used as neutral style labels, not as character impersonations.",
        "persona_saved": "Persona saved: {persona}.",
        "charity": "{quest}\n\nThis is optional; no donation or proof is requested.",
        "quest_claimed": "Quest complete: +{reward} diamonds. Balance: {balance}.",
        "quest_duplicate": "You already completed that optional quest today.",
        "help": "Commands: /start, /menu, /fortune, /tarot, /horoscope, /palm, /games, /daily, /profile, /leaderboard, /personas, /charity, /last, /cancel. Readings are for entertainment only.",
        "not_ready": "Fortunis8 is not fully configured yet. Please try again later.",
    },
    "ur": {
        "welcome": "Fortunis8 میں خوش آمدید۔ زبان منتخب کریں، پھر مینو استعمال کریں۔",
        "language_saved": "زبان اردو محفوظ کر دی گئی ہے۔",
        "menu": "Fortunis8 مینو — مطالعے اور کھیل صرف تفریح کے لیے ہیں۔",
        "unavailable": "Fortunis8 عارضی طور پر دستیاب نہیں۔ درخواست مکمل ظاہر نہیں کی گئی؛ براہِ کرم بعد میں کوشش کریں۔",
        "private_only": "براہِ کرم Fortunis8 کو نجی Telegram چیٹ میں استعمال کریں۔",
        "daily_done": "آج کا انعام پہلے ہی لیا جا چکا ہے۔",
        "daily_claim": "آج کا انعام: +{reward} ڈائمنڈز۔ مسلسل دن: {streak}۔ بیلنس: {balance}۔",
        "profile": "ڈائمنڈز: {diamonds}\nلیول: {level}\nمسلسل دن: {streak}\nپریمیم مطالعے کے کریڈٹ: {credits}\nکردار: {persona}",
        "no_reading": "ابھی کوئی محفوظ مطالعہ موجود نہیں۔ مینو سے مطالعہ منتخب کریں۔",
        "horoscope_prompt": "تاریخ، وقت اور شہر اس طرح بھیجیں: `YYYY-MM-DD HH:MM, City` (مثال: `1995-08-20 09:30, Lahore`)۔ معلومات صرف ایک بار تفریحی سورج نشان والا متن بنانے کے لیے استعمال ہوں گی اور محفوظ نہیں ہوں گی۔ یہ مکمل فلکیاتی کنڈلی نہیں ہے۔",
        "horoscope_invalid": "فارمیٹ درست نہیں۔ `YYYY-MM-DD HH:MM, City` بھیجیں، مثلاً `1995-08-20 09:30, Lahore`۔ معلومات محفوظ نہیں ہوں گی۔",
        "horoscope_future": "براہِ کرم پیدائش کی درست ماضی کی تاریخ استعمال کریں۔ معلومات محفوظ نہیں ہوں گی۔",
        "cancelled": "زائچہ درج کرنے کا عمل منسوخ کر دیا گیا۔",
        "focus": "ایک موضوع منتخب کریں۔ یہ ہتھیلی سے متاثر تحریری غور ہے؛ ہاتھ کی تصویر کا تجزیہ نہیں ہوتا۔",
        "palm_basic_title": "ہتھیلی سے متاثر بنیادی تفریحی غور",
        "palm_premium_title": "ہتھیلی سے متاثر تفصیلی غور",
        "premium_price": "ایک تفصیلی مطالعے کے لیے موضوع منتخب کریں ({price} Telegram Stars)۔ ادائیگی صرف اس مطالعے کے لیے ہے؛ ڈائمنڈز فروخت نہیں ہوتے۔",
        "credits_available": "آپ کے پاس {credits} پریمیم مطالعے کا کریڈٹ ہے۔ استعمال کے لیے موضوع منتخب کریں۔",
        "payment_credit": "ادائیگی کی تصدیق ہو گئی۔ آپ کا تفصیلی مطالعہ نیچے ہے۔ باقی کریڈٹ: {credits}۔",
        "premium_update_duplicate": "یہ Telegram درخواست پہلے ہی پراسیس ہو چکی ہے۔ تازہ ترین محفوظ مطالعے کے لیے /last بھیجیں۔",
        "payment_verified_credit_pending": "ادائیگی کی تصدیق ہو گئی اور ایک مطالعے کا کریڈٹ تیار ہے۔ مینو میں Premium palm reading کھول کر استعمال کریں۔",
        "payment_duplicate": "یہ Telegram Stars ادائیگی پہلے ہی پراسیس ہو چکی ہے۔ تازہ ترین محفوظ مطالعے کے لیے /last بھیجیں۔",
        "payment_invalid": "Fortunis8 database اس ادائیگی کی تصدیق نہیں کر سکا۔ دوبارہ ادائیگی نہ کریں؛ بوٹ کے مالک سے transaction چیک کروائیں۔",
        "payment_unavailable": "ادائیگی کی تصدیق عارضی طور پر دستیاب نہیں۔ براہِ کرم بعد میں کوشش کریں۔",
        "invoice_unavailable": "ابھی Stars invoice نہیں بن سکا۔ آپ سے ادائیگی نہیں لی گئی۔",
        "precheckout_failed": "یہ Stars invoice غلط یا expired ہے۔ ادائیگی نہیں لی گئی۔",
        "game_choose": "بلا معاوضہ مہارت کا کھیل منتخب کریں۔ مشکل سطح پر درست جواب کے زیادہ پوائنٹس ہیں؛ پوائنٹس کی نقد قیمت نہیں۔",
        "game_question": "{difficulty} چیلنج: {question}",
        "game_correct": "درست۔ +{reward} ڈائمنڈز۔ بیلنس: {balance}۔",
        "game_wrong": "جواب درست نہیں۔ کوئی ڈائمنڈ نہیں کٹے؛ دوسرا چیلنج آزمائیں۔",
        "game_expired": "یہ چیلنج ختم ہو گیا۔ مینو سے نیا شروع کریں۔",
        "game_used": "یہ چیلنج پہلے جمع کیا جا چکا ہے۔",
        "leaderboard": "گمنام لیڈر بورڈ (صرف ڈائمنڈز):\n{rows}\n\nآپ کا مقام: {rank}",
        "leaderboard_empty": "لیڈر بورڈ ابھی خالی ہے۔",
        "personas": "کردار منتخب کریں۔ نام صرف غیر جانب دار انداز کے labels ہیں، کردار کی نقل نہیں۔",
        "persona_saved": "کردار محفوظ ہو گیا: {persona}۔",
        "charity": "{quest}\n\nیہ اختیاری ہے؛ عطیہ یا ثبوت درکار نہیں۔",
        "quest_claimed": "مہم مکمل: +{reward} ڈائمنڈز۔ بیلنس: {balance}۔",
        "quest_duplicate": "آپ آج یہ اختیاری مہم پہلے مکمل کر چکے ہیں۔",
        "help": "کمانڈز: /start، /menu، /fortune، /tarot، /horoscope، /palm، /games، /daily، /profile، /leaderboard، /personas، /charity، /last، /cancel۔ تمام مطالعے صرف تفریح کے لیے ہیں۔",
        "not_ready": "Fortunis8 کی مکمل ترتیب ابھی دستیاب نہیں۔ براہِ کرم بعد میں کوشش کریں۔",
    },
}

FOCUS_LABELS = {
    "en": {"general": "general", "love": "relationships", "work": "work", "growth": "personal growth"},
    "ur": {"general": "عمومی", "love": "رشتے", "work": "کام", "growth": "ذاتی ترقی"},
}
GAME_TEXT = {
    "en": {
        "easy": ("What is 2 + 2?", ["3", "4", "5"]),
        "hard": ("What is the square root of 144?", ["10", "12", "14"]),
        "easy_label": "Easy",
        "hard_label": "Hard",
    },
    "ur": {
        "easy": ("2 + 2 کتنے ہوتے ہیں؟", ["3", "4", "5"]),
        "hard": ("144 کا مربع جذر کیا ہے؟", ["10", "12", "14"]),
        "easy_label": "آسان",
        "hard_label": "مشکل",
    },
}
STYLE_UR = {
    "Mario": "خوش مزاج اور عملی", "Tarzan": "دلیر اور فطرت دوست",
    "Hercules": "مستقل مزاج اور حوصلہ افزا", "Dragon": "پرسکون اور چوکس",
    "Ninja": "خاموش اور یکسو", "Wizard": "متجسس اور غوروفکر کرنے والا",
    "Phoenix": "پرامید اور ثابت قدم", "Spartan": "منظم اور صاف گو",
    "Viking": "مہم جو اور وفادار", "Samurai": "صابر اور بااصول",
    "Pirate": "شوخ اور وسائل والا", "Jedi": "متوازن اور عکاس",
}


def _store(context: CallbackContext) -> SupabaseRestUserStore | None:
    return context.application.bot_data.get("fortunis8_store")


def _lang(context: CallbackContext) -> str:
    return context.user_data.get("fortunis8_language", "en")


def _is_private(update: Update) -> bool:
    return update.effective_chat is not None and update.effective_chat.type == "private"


def _account_menu(language: str) -> InlineKeyboardMarkup:
    labels = menu_translations(language)
    text = TEXT[language]
    rows = [
        [InlineKeyboardButton(labels["fortune"], callback_data="f8:fortune"), InlineKeyboardButton(labels["tarot"], callback_data="f8:tarot")],
        [InlineKeyboardButton(labels["palm"], callback_data="f8:palm_basic"), InlineKeyboardButton(text["palm_premium_title"], callback_data="f8:palm_premium")],
        [InlineKeyboardButton(labels["horoscope"], callback_data="f8:horoscope"), InlineKeyboardButton(labels["skill_game"], callback_data="f8:games")],
        [InlineKeyboardButton("Daily reward" if language == "en" else "روزانہ انعام", callback_data="f8:daily"), InlineKeyboardButton("Leaderboard" if language == "en" else "لیڈر بورڈ", callback_data="f8:leaderboard")],
        [InlineKeyboardButton(labels["personas"], callback_data="f8:personas"), InlineKeyboardButton(labels["charity_quest"], callback_data="f8:charity")],
        [InlineKeyboardButton("Language / زبان", callback_data="f8:language")],
    ]
    return InlineKeyboardMarkup(rows)


def _language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("English", callback_data="lang:en"),
        InlineKeyboardButton("اردو", callback_data="lang:ur"),
    ]])


def _focus_keyboard(mode: str, language: str) -> InlineKeyboardMarkup:
    labels = FOCUS_LABELS[language]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels["general"], callback_data=f"palm:focus:{mode}:general"), InlineKeyboardButton(labels["love"], callback_data=f"palm:focus:{mode}:love")],
        [InlineKeyboardButton(labels["work"], callback_data=f"palm:focus:{mode}:work"), InlineKeyboardButton(labels["growth"], callback_data=f"palm:focus:{mode}:growth")],
    ])


def _with_persona(text: str, persona: str, language: str) -> str:
    if language == "ur":
        return f"{text}\n\nمنتخب رہنما: {persona} — {STYLE_UR.get(persona, 'متوازن')} انداز۔"
    return f"{text}\n\nYour guide, {persona}, brings a {persona_style(persona)} lens."


async def _require_store(update: Update, context: CallbackContext) -> SupabaseRestUserStore | None:
    store = _store(context)
    if store is None:
        if update.effective_message:
            await update.effective_message.reply_text(TEXT[_lang(context)]["not_ready"])
        return None
    return store


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update):
        if update.effective_message:
            await update.effective_message.reply_text(TEXT["en"]["private_only"])
        return
    store = await _require_store(update, context)
    if store is None:
        return
    user = update.effective_user
    try:
        language = await store.get_or_create_language(user.id)
        await store.ensure_account(user.id)
    except (PersistenceError, ValueError):
        logger.warning("Fortunis8 onboarding persistence failed.")
        await update.effective_message.reply_text(TEXT["en"]["unavailable"])
        return
    context.user_data["fortunis8_language"] = language
    await update.effective_message.reply_text(TEXT[language]["welcome"], reply_markup=_language_keyboard())


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update):
        await update.effective_message.reply_text(TEXT["en"]["private_only"])
        return
    language = _lang(context)
    await update.effective_message.reply_text(TEXT[language]["menu"], reply_markup=_account_menu(language))


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    if not _is_private(update):
        await query.edit_message_text(TEXT["en"]["private_only"])
        return
    language = {"lang:en": "en", "lang:ur": "ur"}.get(query.data or "")
    if language is None:
        return
    store = _store(context)
    if store is None:
        await query.edit_message_text(TEXT[language]["not_ready"])
        return
    try:
        saved = await store.set_language(update.effective_user.id, language)
        await store.ensure_account(update.effective_user.id)
    except (PersistenceError, ValueError):
        logger.warning("Fortunis8 language persistence failed.")
        await query.edit_message_text(TEXT[language]["unavailable"])
        return
    context.user_data["fortunis8_language"] = saved
    await query.edit_message_text(TEXT[saved]["language_saved"], reply_markup=_account_menu(saved))


async def fortune_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    user = update.effective_user
    language = _lang(context)
    try:
        account = await store.get_account(user.id)
        day = datetime.now(timezone.utc).date().isoformat()
        content = _with_persona(fortune(language, f"fortune:{user.id}:{day}"), account["selected_persona"], language)
        await store.save_reading(user.id, "horoscope", "Fortune", content)
    except (PersistenceError, ValueError, KeyError):
        logger.warning("Fortune flow persistence failed.")
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    await update.effective_message.reply_text(content)


async def tarot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    user = update.effective_user
    language = _lang(context)
    try:
        account = await store.get_account(user.id)
        content = _with_persona(tarot(language, f"tarot:{user.id}:{uuid.uuid4()}"), account["selected_persona"], language)
        await store.save_reading(user.id, "tarot", "Tarot guidance", content)
    except (PersistenceError, ValueError, KeyError):
        logger.warning("Tarot flow persistence failed.")
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    await update.effective_message.reply_text(content)


def _horoscope_input_parts(raw: str) -> tuple[date, time, str]:
    pieces = raw.strip().split(maxsplit=2)
    if len(pieces) != 3:
        raise ValueError("Expected date, time, and location.")
    birth_date = date.fromisoformat(pieces[0])
    birth_time = datetime.strptime(pieces[1].rstrip(","), "%H:%M").time()
    location = " ".join(pieces[2].lstrip(", ").split())
    if not location or len(location) > 120:
        raise ValueError("Invalid location.")
    if birth_date > date.today() or birth_date < date(1900, 1, 1):
        raise OverflowError("Birth date outside supported range.")
    return birth_date, birth_time, location


async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update):
        if update.effective_message:
            await update.effective_message.reply_text(TEXT["en"]["private_only"])
        return
    language = _lang(context)
    raw = " ".join(context.args) if context.args else ""
    if raw:
        context.user_data["fortunis8_awaiting_horoscope"] = True
        await horoscope_input(update, context, raw=raw)
        return
    context.user_data["fortunis8_awaiting_horoscope"] = True
    await update.effective_message.reply_text(TEXT[language]["horoscope_prompt"])


async def horoscope_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, raw: str | None = None
) -> None:
    store = await _require_store(update, context)
    if store is None:
        context.user_data.pop("fortunis8_awaiting_horoscope", None)
        return
    language = _lang(context)
    text = raw if raw is not None else (update.effective_message.text or "")
    try:
        birth_date, birth_time, location = _horoscope_input_parts(text)
    except OverflowError:
        await update.effective_message.reply_text(TEXT[language]["horoscope_future"])
        return
    except (ValueError, TypeError):
        await update.effective_message.reply_text(TEXT[language]["horoscope_invalid"])
        return
    try:
        account = await store.get_account(update.effective_user.id)
        sign = sun_sign(birth_date)
        content = _with_persona(
            horoscope_reading(birth_date, birth_time.strftime("%H:%M"), location, language),
            account["selected_persona"], language,
        )
        # Birth date, time, and location are deliberately not retained.
        await store.save_reading(
            update.effective_user.id, "horoscope", "Horoscope-style reading", content,
            metadata={"sun_sign": sign},
        )
    except (PersistenceError, ValueError, KeyError):
        logger.warning("Horoscope flow persistence failed.")
        context.user_data.pop("fortunis8_awaiting_horoscope", None)
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    context.user_data.pop("fortunis8_awaiting_horoscope", None)
    await update.effective_message.reply_text(content)


async def consume_horoscope_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("fortunis8_awaiting_horoscope"):
        return
    await horoscope_input(update, context)
    raise ApplicationHandlerStop


async def cancel_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("fortunis8_awaiting_horoscope", None)
    await update.effective_message.reply_text(TEXT[_lang(context)]["cancelled"])


async def palm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = _lang(context)
    store = await _require_store(update, context)
    if store is None:
        return
    try:
        account = await store.get_account(update.effective_user.id)
    except (PersistenceError, ValueError):
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    credits = int(account.get("premium_reading_credits", 0))
    if credits > 0:
        prompt = TEXT[language]["credits_available"].format(credits=credits) + "\n" + TEXT[language]["focus"]
        mode = "use"
    else:
        prompt = TEXT[language]["premium_price"].format(price=settings.PREMIUM_PALM_PRICE_STARS) + "\n" + TEXT[language]["focus"]
        mode = "buy"
    await update.effective_message.reply_text(prompt, reply_markup=_focus_keyboard(mode, language))


async def _basic_palm(update: Update, context: ContextTypes.DEFAULT_TYPE, focus: str) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    language = _lang(context)
    try:
        account = await store.get_account(update.effective_user.id)
        label = FOCUS_LABELS[language][focus]
        content = _with_persona(palm_reading(label, language, premium=False), account["selected_persona"], language)
        await store.save_reading(update.effective_user.id, "palm_basic", TEXT[language]["palm_basic_title"], content, {"focus": focus})
    except (PersistenceError, ValueError, KeyError):
        logger.warning("Basic palm reading persistence failed.")
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    await update.effective_message.reply_text(content)


async def _create_stars_invoice(
    update: Update, context: ContextTypes.DEFAULT_TYPE, focus: str
) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    user = update.effective_user
    language = _lang(context)
    payload = f"fortunis8:{user.id}:{uuid.uuid4().hex}"
    price = settings.PREMIUM_PALM_PRICE_STARS
    try:
        await store.create_pending_invoice(
            payload=payload, telegram_user_id=user.id, focus=focus, amount_stars=price
        )
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=TEXT[language]["palm_premium_title"][:32],
            description=TEXT[language]["premium_price"].format(price=price)[:255],
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Detailed palm-themed reading", price)],
        )
    except (PersistenceError, ValueError):
        logger.warning("Stars invoice persistence failed.")
        await update.effective_message.reply_text(TEXT[language]["invoice_unavailable"])
    except Exception as exc:
        logger.warning("Telegram invoice send failed (error_type=%s).", type(exc).__name__)
        try:
            await store.cancel_pending_invoice(payload, user.id)
        except PersistenceError:
            logger.warning("Pending Stars invoice cleanup failed.")
        await update.effective_message.reply_text(TEXT[language]["invoice_unavailable"])


async def _redeem_premium(update: Update, context: ContextTypes.DEFAULT_TYPE, focus: str) -> dict[str, Any] | None:
    store = await _require_store(update, context)
    if store is None:
        return None
    language = _lang(context)
    user = update.effective_user
    try:
        account = await store.get_account(user.id)
        label = FOCUS_LABELS[language][focus]
        content = _with_persona(palm_reading(label, language, premium=True), account["selected_persona"], language)
        result = await store.redeem_premium_reading(
            user.id, update.update_id, focus, TEXT[language]["palm_premium_title"], content
        )
    except (PersistenceError, ValueError, KeyError):
        logger.warning("Premium palm reading redemption failed.")
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return None
    if result.get("duplicate"):
        await update.effective_message.reply_text(TEXT[language]["premium_update_duplicate"])
        return result
    if not result.get("ok"):
        await update.effective_message.reply_text(
            TEXT[language]["premium_price"].format(price=settings.PREMIUM_PALM_PRICE_STARS),
            reply_markup=_focus_keyboard("buy", language),
        )
        return None
    await update.effective_message.reply_text(content)
    await update.effective_message.reply_text(
        TEXT[language]["payment_credit"].format(credits=result.get("credits_remaining", 0))
    )
    return result


async def game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, *, from_callback: bool = False) -> None:
    language = _lang(context)
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(GAME_TEXT[language]["easy_label"], callback_data="game:easy"),
        InlineKeyboardButton(GAME_TEXT[language]["hard_label"], callback_data="game:hard"),
    ]])
    message = update.effective_message
    await message.reply_text(TEXT[language]["game_choose"], reply_markup=markup)


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE, difficulty: str) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    if difficulty not in {"easy", "hard"}:
        return
    language = _lang(context)
    game = skill_game(difficulty)
    question, options = GAME_TEXT[language][difficulty]
    correct_answer = str(game["answer"])
    session_id = str(uuid.uuid4())
    reward = int(game["points"])
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    try:
        await store.create_game_session(
            session_id=session_id,
            telegram_user_id=update.effective_user.id,
            game_key="arithmetic",
            difficulty=difficulty,
            prompt=question,
            options=options,
            correct_answer=correct_answer,
            reward_diamonds=reward,
            expires_at=expiry,
        )
    except (PersistenceError, ValueError):
        logger.warning("Skill-game session creation failed.")
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(choice, callback_data=f"answer:{session_id}:{choice}") for choice in options
    ]])
    await update.effective_message.reply_text(
        TEXT[language]["game_question"].format(difficulty=GAME_TEXT[language][f"{difficulty}_label"], question=question),
        reply_markup=keyboard,
    )


async def answer_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not _is_private(update):
        await query.edit_message_text(TEXT["en"]["private_only"])
        return
    parts = (query.data or "").split(":", 2)
    if len(parts) != 3:
        return
    _, session_id, answer = parts
    store = _store(context)
    language = _lang(context)
    if store is None:
        await query.message.reply_text(TEXT[language]["unavailable"])
        return
    try:
        result = await store.complete_game(session_id, update.effective_user.id, answer)
    except (PersistenceError, ValueError):
        logger.warning("Skill-game completion failed.")
        await query.message.reply_text(TEXT[language]["unavailable"])
        return
    if not result.get("ok") and result.get("reason") == "expired":
        await query.edit_message_text(TEXT[language]["game_expired"])
    elif not result.get("ok") and result.get("reason") == "not_found":
        await query.edit_message_text(TEXT[language]["game_used"])
    elif result.get("completed") and result.get("reward", 0) == 0 and result.get("correct"):
        await query.edit_message_text(TEXT[language]["game_used"])
    elif result.get("correct"):
        await query.edit_message_text(TEXT[language]["game_correct"].format(
            reward=result.get("reward", 0), balance=result.get("diamonds", 0)
        ))
    else:
        await query.edit_message_text(TEXT[language]["game_wrong"])


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    language = _lang(context)
    try:
        result = await store.claim_daily(update.effective_user.id)
    except (PersistenceError, ValueError):
        logger.warning("Daily reward request failed.")
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    if not result.get("ok"):
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
    elif result.get("claimed"):
        await update.effective_message.reply_text(TEXT[language]["daily_claim"].format(
            reward=result.get("reward", 0), streak=result.get("streak", 0), balance=result.get("diamonds", 0)
        ))
    else:
        await update.effective_message.reply_text(TEXT[language]["daily_done"])


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    language = _lang(context)
    try:
        account = await store.get_account(update.effective_user.id)
    except (PersistenceError, ValueError):
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    await update.effective_message.reply_text(TEXT[language]["profile"].format(
        diamonds=account["diamonds"], level=account["level"], streak=account["streak_count"],
        credits=account["premium_reading_credits"], persona=account["selected_persona"],
    ))


async def last_reading(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    language = _lang(context)
    try:
        reading = await store.get_last_reading(update.effective_user.id)
    except (PersistenceError, ValueError):
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    if not reading:
        await update.effective_message.reply_text(TEXT[language]["no_reading"])
    else:
        await update.effective_message.reply_text(f"{reading['title']}\n\n{reading['content']}")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    language = _lang(context)
    try:
        scores, rank = await store.get_leaderboard(update.effective_user.id)
    except (PersistenceError, ValueError):
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    if not scores:
        await update.effective_message.reply_text(TEXT[language]["leaderboard_empty"])
        return
    rows = "\n".join(f"#{index + 1} — {score}" for index, score in enumerate(scores))
    rank_text = f"#{rank}" if rank is not None else ("not ranked" if language == "en" else "درج نہیں")
    await update.effective_message.reply_text(TEXT[language]["leaderboard"].format(rows=rows, rank=rank_text))


async def persona_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, *, from_callback: bool = False) -> None:
    language = _lang(context)
    names = supported_personas()
    rows = [
        [InlineKeyboardButton(names[index], callback_data=f"persona:{names[index]}") for index in range(offset, min(offset + 3, len(names)))]
        for offset in range(0, len(names), 3)
    ]
    await update.effective_message.reply_text(TEXT[language]["personas"], reply_markup=InlineKeyboardMarkup(rows))


async def charity_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, *, from_callback: bool = False) -> None:
    language = _lang(context)
    labels = {
        "en": [("Kindness", "kindness"), ("Gratitude", "gratitude"), ("Helpful act", "helpful")],
        "ur": [("مہربانی", "kindness"), ("شکرگزاری", "gratitude"), ("مددگار کام", "helpful")],
    }[language]
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data=f"quest:{key}") for label, key in labels
    ]])
    await update.effective_message.reply_text(
        TEXT[language]["charity"].format(quest=charity_quest(language)), reply_markup=markup
    )


async def claim_charity(update: Update, context: ContextTypes.DEFAULT_TYPE, quest_key: str) -> None:
    store = await _require_store(update, context)
    if store is None:
        return
    language = _lang(context)
    try:
        result = await store.claim_charity_quest(update.effective_user.id, quest_key)
    except (PersistenceError, ValueError):
        await update.effective_message.reply_text(TEXT[language]["unavailable"])
        return
    if result.get("claimed"):
        await update.effective_message.reply_text(TEXT[language]["quest_claimed"].format(
            reward=result.get("reward", 0), balance=result.get("diamonds", 0)
        ))
    elif result.get("ok"):
        await update.effective_message.reply_text(TEXT[language]["quest_duplicate"])
    else:
        await update.effective_message.reply_text(TEXT[language]["unavailable"])


async def palm_photo_notice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = _lang(context)
    message = (
        "This version does not analyze or save hand photos. Use /palm for a focus-based text reflection."
        if language == "en"
        else "اس ورژن میں ہاتھ کی تصاویر کا تجزیہ یا محفوظ نہیں کیا جاتا۔ موضوع کے مطابق تحریری غور کے لیے /palm استعمال کریں۔"
    )
    await update.effective_message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(TEXT[_lang(context)]["help"])


async def localized_text_intent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip().lower()
    language = _lang(context)
    if any(term in text for term in ("قسمت", "زائچہ", "زچہ", "آج کا مطالعہ")):
        await fortune_command(update, context)
    elif any(term in text for term in ("ٹیرو", "تاش")):
        await tarot_command(update, context)
    elif any(term in text for term in ("پروفائل", "میرا بیلنس", "میرے ڈائمنڈ")):
        await profile_command(update, context)
    elif any(term in text for term in ("روزانہ انعام", "روزانہ انعام لیں")):
        await daily_command(update, context)
    elif any(term in text for term in ("مہارت کا کھیل", "کھیل شروع")):
        await game_menu(update, context)
    elif any(term in text for term in ("خیرات", "نیکی کی مہم")):
        await charity_menu(update, context)


async def route_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_private(update):
        await query.edit_message_text(TEXT["en"]["private_only"])
        return
    data = query.data or ""
    language = _lang(context)
    if data == "f8:fortune":
        await fortune_command(update, context)
    elif data == "f8:tarot":
        await tarot_command(update, context)
    elif data == "f8:palm_basic":
        await query.message.reply_text(TEXT[language]["focus"], reply_markup=_focus_keyboard("basic", language))
    elif data == "f8:palm_premium":
        await palm_command(update, context)
    elif data == "f8:horoscope":
        await horoscope_start(update, context)
    elif data == "f8:games":
        await game_menu(update, context, from_callback=True)
    elif data == "f8:daily":
        await daily_command(update, context)
    elif data == "f8:leaderboard":
        await leaderboard(update, context)
    elif data == "f8:personas":
        await persona_menu(update, context, from_callback=True)
    elif data == "f8:charity":
        await charity_menu(update, context, from_callback=True)
    elif data == "f8:language":
        await query.message.reply_text(TEXT[language]["welcome"], reply_markup=_language_keyboard())
    elif data.startswith("palm:focus:"):
        parts = data.split(":")
        if len(parts) != 4 or parts[3] not in FOCUS_LABELS[language]:
            return
        mode, focus = parts[2], parts[3]
        if mode == "basic":
            await _basic_palm(update, context, focus)
        elif mode == "buy":
            await _create_stars_invoice(update, context, focus)
        elif mode == "use":
            await _redeem_premium(update, context, focus)
    elif data.startswith("game:"):
        await start_game(update, context, data.split(":", 1)[1])
    elif data.startswith("answer:"):
        await answer_game(update, context)
    elif data.startswith("persona:"):
        persona = data.split(":", 1)[1]
        if persona not in supported_personas():
            return
        store = _store(context)
        if store is None:
            await query.message.reply_text(TEXT[language]["not_ready"])
            return
        try:
            await store.set_persona(update.effective_user.id, persona)
        except (PersistenceError, ValueError):
            await query.message.reply_text(TEXT[language]["unavailable"])
            return
        await query.message.reply_text(TEXT[language]["persona_saved"].format(persona=persona))
    elif data.startswith("quest:"):
        await claim_charity(update, context, data.split(":", 1)[1])


async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    store = _store(context)
    language = _lang(context)
    if store is None:
        await query.answer(ok=False, error_message=TEXT[language]["payment_unavailable"])
        return
    try:
        invoice = await store.get_valid_invoice(query.invoice_payload, query.from_user.id)
        valid = bool(
            invoice
            and invoice.get("currency") == "XTR"
            and invoice.get("amount_stars") == query.total_amount
        )
    except (PersistenceError, ValueError):
        valid = False
    if valid:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message=TEXT[language]["precheckout_failed"])


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.effective_message.successful_payment
    store = _store(context)
    language = _lang(context)
    if store is None:
        await update.effective_message.reply_text(TEXT[language]["payment_unavailable"])
        return
    try:
        result = await store.record_star_payment(
            update.effective_user.id,
            payment.invoice_payload,
            payment.telegram_payment_charge_id,
            payment.total_amount,
            payment.currency,
        )
    except (PersistenceError, ValueError):
        logger.warning("Successful Telegram Stars payment could not be recorded.")
        await update.effective_message.reply_text(TEXT[language]["payment_unavailable"])
        return
    if not result.get("ok"):
        await update.effective_message.reply_text(TEXT[language]["payment_invalid"])
        return
    if not result.get("credited"):
        await update.effective_message.reply_text(TEXT[language]["payment_duplicate"])
        return
    focus = result.get("focus")
    if focus not in FOCUS_LABELS[language]:
        await update.effective_message.reply_text(TEXT[language]["payment_verified_credit_pending"])
        return
    # Redeem and persist the reading atomically. If this step fails, the paid credit remains.
    try:
        account = await store.get_account(update.effective_user.id)
        content = _with_persona(
            palm_reading(FOCUS_LABELS[language][focus], language, premium=True),
            account["selected_persona"], language,
        )
        redeemed = await store.redeem_premium_reading(
            update.effective_user.id, update.update_id, focus, TEXT[language]["palm_premium_title"], content
        )
    except (PersistenceError, ValueError, KeyError):
        logger.warning("Premium reading delivery preparation failed after payment.")
        await update.effective_message.reply_text(TEXT[language]["payment_verified_credit_pending"])
        return
    if redeemed.get("duplicate"):
        await update.effective_message.reply_text(TEXT[language]["premium_update_duplicate"])
        return
    if not redeemed.get("ok"):
        await update.effective_message.reply_text(TEXT[language]["payment_verified_credit_pending"])
        return
    await update.effective_message.reply_text(content)
    await update.effective_message.reply_text(TEXT[language]["payment_credit"].format(
        credits=redeemed.get("credits_remaining", 0)
    ))


async def prime_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Load the saved language before other handlers on a fresh process session."""
    user = update.effective_user
    if user is None:
        return
    chat = update.effective_chat
    if chat is not None and chat.type != "private":
        return
    if context.user_data.get("fortunis8_language") in {"en", "ur"}:
        return
    store = _store(context)
    if store is None:
        return
    try:
        context.user_data["fortunis8_language"] = await store.get_or_create_language(user.id)
    except (PersistenceError, ValueError):
        logger.warning("Saved language could not be loaded.")


async def reject_non_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message is not None:
        await update.effective_message.reply_text(TEXT["en"]["private_only"])


async def shutdown_store(application: Application) -> None:
    store = application.bot_data.get("fortunis8_store")
    if store is not None:
        await store.close()


def register_fortunis8_handlers(application: Application) -> None:
    """Add new feature handlers before the original English MVP handlers."""
    secret = getattr(settings, "SUPABASE_SECRET_KEY", None)
    url = getattr(settings, "SUPABASE_URL", None)
    store = SupabaseRestUserStore(url, secret) if url and secret else None
    if not hasattr(application, "bot_data"):
        application.bot_data = {}
    application.bot_data["fortunis8_store"] = store
    try:
        application.add_handler(TypeHandler(Update, prime_user), group=-1)
    except TypeError:
        # Minimal test builders may not implement handler groups.
        pass

    try:
        application.add_handler(
            MessageHandler(
                filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
                consume_horoscope_input,
            ),
            group=-2,
        )
    except TypeError:
        # Minimal test doubles do not implement handler groups.
        pass
    application.add_handler(CallbackQueryHandler(choose_language, pattern=r"^lang:(?:en|ur)$"))
    application.add_handler(CallbackQueryHandler(route_callback, pattern=r"^(?:f8:|palm:|game:|answer:|persona:|quest:).+"))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.PHOTO, palm_photo_notice))
    application.add_handler(MessageHandler(filters.COMMAND & ~filters.ChatType.PRIVATE, reject_non_private))

    commands = [
        ("start", start), ("menu", menu), ("help", help_command),
        ("fortune", fortune_command), ("tarot", tarot_command),
        ("horoscope", horoscope_start), ("cancel", cancel_horoscope),
        ("palm", palm_command), ("games", game_menu), ("daily", daily_command),
        ("reward", daily_command), ("profile", profile_command),
        ("leaderboard", leaderboard), ("personas", persona_menu),
        ("charity", charity_menu), ("quests", charity_menu),
        ("personalize", persona_menu), ("last", last_reading),
    ]
    for command, callback in commands:
        application.add_handler(CommandHandler(command, callback, filters=filters.ChatType.PRIVATE))
    urdu_intents = filters.Regex(r"(قسمت|زائچہ|زچہ|آج کا مطالعہ|ٹیرو|تاش|پروفائل|میرا بیلنس|میرے ڈائمنڈ|روزانہ انعام|مہارت کا کھیل|کھیل شروع|خیرات|نیکی کی مہم)")
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND & urdu_intents, localized_text_intent))
