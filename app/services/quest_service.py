from __future__ import annotations

from datetime import datetime
from typing import Any

from app.config import settings
from app.db.supabase_client import supabase
from app.services.rewards_service import award_diamonds_and_level
from app.services.user_service import ensure_profile, update_profile

LOCAL_QUESTS: dict[str, list[dict[str, Any]]] = {}

DEFAULT_QUESTS = [
    {
        "key": "daily_fortune",
        "title": "Daily Fortune",
        "description": "Complete one horoscope reading today.",
        "reward_diamonds": 25,
        "status": "active",
    },
    {
        "key": "tarot_focus",
        "title": "Tarot Focus",
        "description": "Ask a tarot question and receive guidance.",
        "reward_diamonds": 20,
        "status": "active",
    },
    {
        "key": "streak_mastery",
        "title": "Streak Mastery",
        "description": "Keep your fortune streak alive for three days.",
        "reward_diamonds": 35,
        "status": "active",
    },
    {
        "key": "kindness_quest",
        "title": "Kindness Quest",
        "description": "Complete a small act of kindness and reflect on it.",
        "reward_diamonds": 30,
        "status": "active",
    },
]

INTENT_MAP = {
    "daily_fortune": ["daily fortune", "fortune", "horoscope", "reading for today", "my fortune today"],
    "tarot_focus": ["tarot", "tarot card", "draw tarot", "my tarot"],
    "streak_mastery": ["streak", "daily streak", "keep going", "consistency"],
    "kindness_quest": ["kindness", "help someone", "good deed", "charity", "do good"],
}


def _get_local_quests_for_user(user) -> list[dict[str, Any]]:
    key = str(user.id)
    if key not in LOCAL_QUESTS:
        LOCAL_QUESTS[key] = [
            {**quest, "user_id": key, "completed_at": None}
            for quest in DEFAULT_QUESTS
        ]
    return LOCAL_QUESTS[key]


def _quest_matches(quest: dict[str, Any], quest_key: str) -> bool:
    return quest.get("key") == quest_key or quest.get("title", "").lower() == quest_key.lower()


def detect_quest_intent(message: str) -> str | None:
    """Map natural-language text to a Fortunis8 quest key."""
    text = (message or "").lower()

    for quest_key, phrases in INTENT_MAP.items():
        if any(phrase in text for phrase in phrases):
            return quest_key
    return None


def _sync_local_to_profile(user, profile: dict[str, Any], completed_quest: dict[str, Any]) -> dict[str, Any]:
    current_balance = int(profile.get("diamonds", 0) or 0)
    new_balance, new_level = award_diamonds_and_level(current_balance, int(completed_quest["reward_diamonds"]))

    updated = update_profile(
        user,
        diamonds=new_balance,
        level=new_level,
        streak_count=profile.get("streak_count", 0),
    )
    return {**profile, **updated, "diamonds": new_balance, "level": new_level}


def get_user_quests(user) -> list[dict[str, Any]]:
    profile = ensure_profile(user)

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return _get_local_quests_for_user(user)

    try:
        response = (
            supabase.table("quests")
            .select("*")
            .eq("user_id", profile["id"])
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data

        rows = [
            {
                "user_id": profile["id"],
                "title": quest["title"],
                "description": quest["description"],
                "reward_diamonds": quest["reward_diamonds"],
                "status": quest["status"],
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": None,
            }
            for quest in DEFAULT_QUESTS
        ]
        inserted = supabase.table("quests").insert(rows).execute()
        return inserted.data or rows

    except Exception:
        return _get_local_quests_for_user(user)


def get_quest_summary(user) -> str:
    quests = get_user_quests(user)
    lines = ["Your current quests:"]

    for quest in quests:
        status = "✅ completed" if quest.get("status") == "completed" else "⏳ active"
        lines.append(f"- {quest.get('title')} [{status}]")

    return "\n".join(lines)


def complete_quest(user, quest_key: str) -> dict[str, Any]:
    profile = ensure_profile(user)
    quests = get_user_quests(user)

    for quest in quests:
        if not _quest_matches(quest, quest_key):
            continue

        if quest.get("status") == "completed":
            return {
                "completed": False,
                "title": quest.get("title"),
                "reward_diamonds": quest.get("reward_diamonds", 0),
                "message": "This quest has already been completed.",
            }

        quest["status"] = "completed"
        quest["completed_at"] = datetime.utcnow().isoformat()

        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                supabase.table("quests").update({
                    "status": "completed",
                    "completed_at": quest["completed_at"],
                }).eq("user_id", profile["id"]).eq("title", quest["title"]).execute()
            except Exception:
                pass

        updated_profile = _sync_local_to_profile(user, profile, quest)
        return {
            "completed": True,
            "title": quest.get("title"),
            "reward_diamonds": quest.get("reward_diamonds", 0),
            "message": f"Quest complete: {quest.get('title')} (+{quest.get('reward_diamonds', 0)} diamonds)",
            "profile": updated_profile,
        }

    fallback_quest = {
        "key": quest_key,
        "title": quest_key.replace("_", " ").title(),
        "description": "Mystic challenge complete.",
        "reward_diamonds": 20,
        "status": "completed",
    }
    updated_profile = _sync_local_to_profile(user, profile, fallback_quest)
    return {
        "completed": True,
        "title": fallback_quest["title"],
        "reward_diamonds": fallback_quest["reward_diamonds"],
        "message": f"Quest complete: {fallback_quest['title']} (+{fallback_quest['reward_diamonds']} diamonds)",
        "profile": updated_profile,
    }
