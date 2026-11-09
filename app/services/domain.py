"""Pure domain helpers for an entertainment-only Telegram bot.

This module deliberately makes no network calls, stores no birth data, and does not
process images. The readings are playful prompts, not predictions or advice.
"""

from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
from typing import Mapping, Sequence

SUPPORTED_LANGUAGES = ("en", "ur")

SAFETY_DISCLAIMER = {
    "en": "For entertainment only—this is not a guaranteed prediction, professional advice, or a full astronomical kundli.",
    "ur": "صرف تفریح کے لیے—یہ یقینی پیش گوئی، پیشہ ورانہ مشورہ، یا مکمل فلکیاتی کنڈلی نہیں ہے۔",
}

MENU_TRANSLATIONS = {
    "en": {
        "fortune": "Fortune",
        "tarot": "Tarot",
        "palm": "Palm reading",
        "horoscope": "Horoscope-style reading",
        "skill_game": "Skill game",
        "charity_quest": "Positive charity quest",
        "personas": "Personas",
    },
    "ur": {
        "fortune": "قسمت کا تفریحی پیغام",
        "tarot": "ٹیرو",
        "palm": "ہتھیلی کا مطالعہ",
        "horoscope": "زائچہ طرز کا مطالعہ",
        "skill_game": "مہارت کا کھیل",
        "charity_quest": "مثبت خیراتی مہم",
        "personas": "کردار",
    },
}

PERSONAS = (
    "Mario", "Tarzan", "Hercules", "Dragon", "Ninja", "Wizard",
    "Phoenix", "Spartan", "Viking", "Samurai", "Pirate", "Jedi",
)

PERSONA_STYLES = {
    "Mario": "cheerful and practical",
    "Tarzan": "bold and nature-minded",
    "Hercules": "steady and encouraging",
    "Dragon": "calm and watchful",
    "Ninja": "quiet and focused",
    "Wizard": "curious and thoughtful",
    "Phoenix": "hopeful and resilient",
    "Spartan": "disciplined and direct",
    "Viking": "adventurous and loyal",
    "Samurai": "patient and honorable",
    "Pirate": "playful and resourceful",
    "Jedi": "balanced and reflective",
}

FORTUNE_MESSAGES = {
    "en": (
        "A small change of routine may make today feel brighter.",
        "Notice a useful question before rushing toward an answer.",
        "A kind conversation could open a fresh perspective.",
        "Celebrate progress that is real, even if it is modest.",
    ),
    "ur": (
        "معمول میں ایک چھوٹی تبدیلی آج کو روشن محسوس کرا سکتی ہے۔",
        "جواب کی طرف جلدی سے پہلے ایک مفید سوال پر غور کریں۔",
        "ایک مہربان گفتگو نیا نقطۂ نظر کھول سکتی ہے۔",
        "حقیقی پیش رفت کا جشن منائیں، چاہے وہ معمولی ہی ہو۔",
    ),
}

TAROT_MESSAGES = {
    "en": ("The Lantern: explore one clear next step.", "The Bridge: balance two viewpoints.", "The Seed: give a small idea patient attention."),
    "ur": ("چراغ: اگلے ایک واضح قدم کو تلاش کریں۔", "پل: دو نقطۂ نظر میں توازن رکھیں۔", "بیج: ایک چھوٹے خیال کو صبر سے وقت دیں۔"),
}

PALM_MESSAGES = {
    "en": {
        "basic": "A playful palm-themed reflection for {focus}: notice patterns, choices, and what you can influence.",
        "premium": "A longer palm-themed reflection for {focus}: compare your priorities, try one gentle experiment, and review how it feels. No image processing is performed.",
    },
    "ur": {
        "basic": "{focus} کے لیے ہتھیلی سے متاثر ایک تفریحی غور: نمونوں، انتخابوں اور اپنے اختیار والی چیزوں کو دیکھیں۔",
        "premium": "{focus} کے لیے ہتھیلی سے متاثر تفصیلی غور: ترجیحات کا موازنہ کریں، ایک نرم تجربہ کریں، اور احساس کا جائزہ لیں۔ تصویر پر کارروائی نہیں کی جاتی۔",
    },
}

CHARITY_QUEST_MESSAGES = {
    "en": ("Optional quest: share a kind word or support a cause you trust—only if you want to.",),
    "ur": ("اختیاری مہم: کوئی حوصلہ افزا بات کہیں یا اپنی پسند کے مقصد کی مدد کریں—صرف اگر آپ چاہیں۔",),
}


def _language(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    return language


def menu_translations(language: str = "en") -> Mapping[str, str]:
    """Return a copy of menu labels for English (en) or Urdu (ur)."""
    return dict(MENU_TRANSLATIONS[_language(language)])


def supported_personas() -> tuple[str, ...]:
    return PERSONAS


def persona_style(persona: str, language: str = "en") -> str:
    """Return a neutral style descriptor without imitating a franchise voice."""
    _language(language)
    if persona not in PERSONA_STYLES:
        raise ValueError(f"Unknown persona: {persona}")
    return PERSONA_STYLES[persona]


def _index(seed: str, size: int) -> int:
    return int.from_bytes(sha256(seed.encode("utf-8")).digest()[:8], "big") % size


def fortune(language: str = "en", seed: str = "today") -> str:
    lang = _language(language)
    return f"{FORTUNE_MESSAGES[lang][_index(seed, len(FORTUNE_MESSAGES[lang]))]} {SAFETY_DISCLAIMER[lang]}"


def tarot(language: str = "en", seed: str = "today") -> str:
    lang = _language(language)
    return f"{TAROT_MESSAGES[lang][_index(seed, len(TAROT_MESSAGES[lang]))]} {SAFETY_DISCLAIMER[lang]}"


def palm_reading(focus: str, language: str = "en", premium: bool = False) -> str:
    """Create text from a user-chosen, non-identifying focus; never accepts/processes an image."""
    lang = _language(language)
    clean_focus = " ".join(focus.split())
    if not clean_focus or len(clean_focus) > 80:
        raise ValueError("focus must be 1–80 non-identifying characters")
    tier = "premium" if premium else "basic"
    return f"{PALM_MESSAGES[lang][tier].format(focus=clean_focus)} {SAFETY_DISCLAIMER[lang]}"


def _coerce_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def sun_sign(birth_date: date | datetime | str) -> str:
    """Return a western sun-sign label using conventional tropical date boundaries."""
    day = _coerce_date(birth_date)
    month_day = (day.month, day.day)
    boundaries = (
        ((1, 20), "Aquarius"), ((2, 19), "Pisces"), ((3, 21), "Aries"),
        ((4, 20), "Taurus"), ((5, 21), "Gemini"), ((6, 21), "Cancer"),
        ((7, 23), "Leo"), ((8, 23), "Virgo"), ((9, 23), "Libra"),
        ((10, 23), "Scorpio"), ((11, 22), "Sagittarius"), ((12, 22), "Capricorn"),
    )
    for boundary, sign in reversed(boundaries):
        if month_day >= boundary:
            return sign
    return "Capricorn"


def horoscope_reading(birth_date: date | datetime | str, birth_time: str, location: str, language: str = "en") -> str:
    """Return a deterministic horoscope-style reading without retaining inputs or claiming a kundli."""
    lang = _language(language)
    clean_location = " ".join(location.split())
    if not clean_location or len(clean_location) > 120:
        raise ValueError("location must be 1–120 characters")
    sign = sun_sign(birth_date)
    seed = f"{_coerce_date(birth_date).isoformat()}|{birth_time.strip()}|{clean_location}"
    themes = {
        "en": ("curiosity", "patience", "clear communication", "steady creativity"),
        "ur": ("تجسس", "صبر", "واضح ابلاغ", "مستقل تخلیق"),
    }[lang]
    theme = themes[_index(seed, len(themes))]
    if lang == "ur":
        text = f"آپ کا تفریحی سورج نشان {sign} ہے؛ آج کا ذاتی موضوع {theme} ہے۔ وقت اور مقام صرف اس متن کو متعین کرنے کے لیے استعمال ہوئے ہیں۔"
    else:
        text = f"Your entertainment sun sign is {sign}; today’s personalized theme is {theme}. Time and location only shape this text."
    return f"{text} {SAFETY_DISCLAIMER[lang]}"


SKILL_GAMES = {
    "easy": {"question": "What is 2 + 2?", "answer": "4", "points": 10},
    "hard": {"question": "What is the square root of 144?", "answer": "12", "points": 50},
}


def skill_game(level: str = "easy") -> Mapping[str, object]:
    if level not in SKILL_GAMES:
        raise ValueError("level must be easy or hard")
    return dict(SKILL_GAMES[level])


def check_skill_answer(level: str, answer: str) -> int:
    game = skill_game(level)
    return int(game["points"]) if answer.strip().casefold() == str(game["answer"]).casefold() else 0


def charity_quest(language: str = "en") -> str:
    return CHARITY_QUEST_MESSAGES[_language(language)][0]
