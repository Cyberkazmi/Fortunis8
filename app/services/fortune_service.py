from app.db.supabase_client import supabase
from app.config import settings

PERSONAS = {
    "Oracle of Light": ["oracle of light", "oracle", "light"],
    "Sun Warrior": ["sun warrior", "warrior", "sun"],
    "Moon Reader": ["moon reader", "moon", "reader"],
    "Guardian of Fortune": ["guardian of fortune", "guardian", "fortune guardian"],
    "Shadow Seer": ["shadow seer", "shadow", "seer"],
}

DEFAULT_PERSONA = "Oracle of Light"

MOOD_ALIASES = {
    "balanced": ["balanced", "calm", "peaceful", "steady", "centered"],
    "hopeful": ["hopeful", "optimistic", "uplifted", "bright"],
    "stressed": ["stressed", "overwhelmed", "anxious", "tense", "burned out"],
    "lonely": ["lonely", "isolated", "empty", "unseen"],
    "ambitious": ["ambitious", "driven", "focused", "determined"],
    "sad": ["sad", "down", "heavy", "hurt", "low"],
    "curious": ["curious", "wondering", "questioning", "intrigued"],
}

DEFAULT_MOOD = "balanced"


def normalize_persona(value) -> str:
    if not value:
        return DEFAULT_PERSONA
    text = str(value).strip().lower()
    for canonical, aliases in PERSONAS.items():
        if text in aliases or text == canonical.lower():
            return canonical
    return DEFAULT_PERSONA


def normalize_mood(value) -> str:
    if not value:
        return DEFAULT_MOOD
    text = str(value).strip().lower()
    for canonical, aliases in MOOD_ALIASES.items():
        if text in aliases or text == canonical:
            return canonical
    return DEFAULT_MOOD


def ensure_profile(user) -> dict:
    """Create or fetch the Telegram user's Fortunis8 profile."""
    telegram_id = str(user.id)

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return {
            "telegram_id": telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "zodiac_sign": None,
            "selected_persona": DEFAULT_PERSONA,
            "current_mood": DEFAULT_MOOD,
            "diamonds": 0,
            "streak_count": 0,
            "level": 1,
            "local_mode": True,
        }

    try:
        existing = (
            supabase.table("profiles")
            .select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            profile = existing.data[0]
            profile["selected_persona"] = normalize_persona(profile.get("selected_persona"))
            profile["current_mood"] = normalize_mood(profile.get("current_mood"))
            return profile

        payload = {
            "telegram_id": telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "zodiac_sign": None,
            "selected_persona": DEFAULT_PERSONA,
            "current_mood": DEFAULT_MOOD,
            "diamonds": 0,
            "streak_count": 0,
            "level": 1,
        }

        result = supabase.table("profiles").insert(payload).execute()
        if result.data:
            profile = result.data[0]
            profile["selected_persona"] = normalize_persona(profile.get("selected_persona"))
            profile["current_mood"] = normalize_mood(profile.get("current_mood"))
            return profile

        return payload

    except Exception:
        return {
            "telegram_id": telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "zodiac_sign": None,
            "selected_persona": DEFAULT_PERSONA,
            "current_mood": DEFAULT_MOOD,
            "diamonds": 0,
            "streak_count": 0,
            "level": 1,
            "local_mode": True,
        }


def update_profile(user, **fields):
    """Update a Telegram user's profile details in Supabase or local fallback."""
    telegram_id = str(user.id)

    if "selected_persona" in fields:
        fields["selected_persona"] = normalize_persona(fields["selected_persona"])
    if "current_mood" in fields:
        fields["current_mood"] = normalize_mood(fields["current_mood"])

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return {"telegram_id": telegram_id, "local_mode": True, **fields}

    try:
        result = (
            supabase.table("profiles")
            .update(fields)
            .eq("telegram_id", telegram_id)
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception:
        return {"telegram_id": telegram_id, "local_mode": True, **fields}

    return {"telegram_id": telegram_id, **fields}


def get_persona_options() -> list[str]:
    return list(PERSONAS.keys())


def get_mood_options() -> list[str]:
    return list(MOOD_ALIASES.keys())
