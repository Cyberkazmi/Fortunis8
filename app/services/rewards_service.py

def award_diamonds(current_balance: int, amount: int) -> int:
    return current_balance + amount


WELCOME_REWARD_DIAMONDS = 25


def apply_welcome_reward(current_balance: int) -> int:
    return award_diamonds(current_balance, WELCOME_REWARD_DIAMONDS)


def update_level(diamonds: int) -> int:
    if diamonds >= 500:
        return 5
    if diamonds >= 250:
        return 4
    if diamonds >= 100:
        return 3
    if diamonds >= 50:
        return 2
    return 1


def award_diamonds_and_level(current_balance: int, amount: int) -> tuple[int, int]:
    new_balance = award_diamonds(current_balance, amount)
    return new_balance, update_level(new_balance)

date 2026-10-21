from app.db.supabase_client import supabase
from app.config import settings


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
            "selected_persona": "Oracle of Light",
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
            return existing.data[0]

        payload = {
            "telegram_id": telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "zodiac_sign": None,
            "selected_persona": "Oracle of Light",
            "diamonds": 0,
            "streak_count": 0,
            "level": 1,
        }

        result = supabase.table("profiles").insert(payload).execute()
        if result.data:
            return result.data[0]

        return payload

    except Exception:
        return {
            "telegram_id": telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "zodiac_sign": None,
            "selected_persona": "Oracle of Light",
            "diamonds": 0,
            "streak_count": 0,
            "level": 1,
            "local_mode": True,
        }


def update_profile(user, **fields):
    """Update a Telegram user's profile details in Supabase or local fallback."""
    telegram_id = str(user.id)

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
