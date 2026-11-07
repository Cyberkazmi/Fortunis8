from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.profile_service import UserProfile


class SupabaseProfileRepository:
    """Service-side adapter for the additive profile schema.

    The client must be created with a server-only Supabase service-role key.
    Browser requests never supply profile IDs; callers pass the verified auth user ID.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    def _profile_row(self, auth_user_id: str) -> dict[str, Any] | None:
        result = (
            self.client.table("profiles")
            .select("id,auth_user_id,language,timezone")
            .eq("auth_user_id", auth_user_id)
            .limit(1)
            .execute()
        )
        rows = getattr(result, "data", None) or []
        return rows[0] if rows else None

    def get(self, auth_user_id: str) -> UserProfile | None:
        row = self._profile_row(auth_user_id)
        if row is None:
            return None
        profile_id = row["id"]
        preferences = (
            self.client.table("profile_preferences")
            .select("*")
            .eq("user_id", profile_id)
            .limit(1)
            .execute()
        ).data or []
        preference = preferences[0] if preferences else {}
        goals = (
            self.client.table("profile_goals")
            .select("goal_key")
            .eq("user_id", profile_id)
            .eq("active", True)
            .execute()
        ).data or []
        guidance = (
            self.client.table("profile_guidance_modes")
            .select("guidance_mode_key")
            .eq("user_id", profile_id)
            .eq("active", True)
            .execute()
        ).data or []
        belief_mode = _belief_from_guidance(guidance)
        return UserProfile(
            user_id=auth_user_id,
            goals=tuple(item["goal_key"] for item in goals),
            belief_mode=belief_mode,
            rhythm_minutes=preference.get("daily_duration_minutes", 5),
            language=row.get("language", "en"),
            optional_readings=preference.get("use_readings", False),
            delivery_time=None,
            timezone=row.get("timezone", "UTC"),
            current_state=preference.get("current_state_key"),
            preferred_delivery_window=preference.get("preferred_delivery_window", "morning"),
            notification_frequency=preference.get("notification_frequency", "daily"),
            notifications_enabled=preference.get("notifications_enabled", True),
        )

    def save(self, profile: UserProfile) -> UserProfile:
        now = datetime.now(timezone.utc).isoformat()
        profile_row = (
            self.client.table("profiles")
            .upsert(
                {
                    "auth_user_id": profile.user_id,
                    # Legacy Telegram profiles require this column. Web-auth
                    # profiles use a stable namespaced surrogate.
                    "telegram_id": f"web:{profile.user_id}",
                    "language": profile.language,
                    "timezone": profile.timezone or "UTC",
                    "onboarding_status": "confirmed",
                    "updated_at": now,
                },
                on_conflict="auth_user_id",
            )
            .execute()
        )
        rows = getattr(profile_row, "data", None) or []
        persisted = rows[0] if rows else self._profile_row(profile.user_id)
        if not persisted:
            raise RuntimeError("Supabase profile upsert returned no profile row")
        profile_id = persisted["id"]
        self.client.table("profile_preferences").upsert(
            {
                "user_id": profile_id,
                "current_state_key": profile.current_state,
                "daily_duration_minutes": profile.rhythm_minutes,
                "preferred_delivery_window": profile.preferred_delivery_window,
                "notification_frequency": profile.notification_frequency,
                "notifications_enabled": profile.notifications_enabled,
                "use_readings": profile.optional_readings,
                "updated_at": now,
            },
            on_conflict="user_id",
        ).execute()
        self.client.table("profile_goals").delete().eq("user_id", profile_id).execute()
        self.client.table("profile_goals").insert(
            [{"user_id": profile_id, "goal_key": key, "priority": index + 1, "active": True} for index, key in enumerate(profile.goals)]
        ).execute()
        self.client.table("profile_guidance_modes").delete().eq("user_id", profile_id).execute()
        self.client.table("profile_guidance_modes").insert(
            [{"user_id": profile_id, "guidance_mode_key": _guidance_from_belief(profile.belief_mode), "priority": 1, "active": True}]
        ).execute()
        return profile


def _guidance_from_belief(belief_mode: str) -> str:
    return {
        "Scientific": "scientific",
        "Mindfulness": "mindfulness",
        "Spiritual": "spiritual_reflection",
        "Religious": "religious_practice",
        "Practical": "practical",
        "Mixed": "mixed",
    }[belief_mode]


def _belief_from_guidance(rows: list[dict[str, Any]]) -> str:
    return {
        "scientific": "Scientific",
        "mindfulness": "Mindfulness",
        "spiritual_reflection": "Spiritual",
        "religious_practice": "Religious",
        "practical": "Practical",
        "mixed": "Mixed",
    }.get(rows[0].get("guidance_mode_key") if rows else "scientific", "Scientific")
