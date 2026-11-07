from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


PLAN_ROWS: dict[str, dict[str, Any]] = {
    "free": {
        "key": "free",
        "name_en": "Free",
        "name_ur": "مفت",
        "billing_interval": None,
        "price_pkr": 0,
        "price_usd_cents": 0,
        "trial_days": 0,
    },
    "premium_monthly": {
        "key": "premium_monthly",
        "name_en": "Premium Monthly",
        "name_ur": "پریمیم ماہانہ",
        "billing_interval": "month",
        "price_pkr": 499,
        "price_usd_cents": 499,
        "trial_days": 7,
    },
    "premium_yearly": {
        "key": "premium_yearly",
        "name_en": "Premium Yearly",
        "name_ur": "پریمیم سالانہ",
        "billing_interval": "year",
        "price_pkr": 3999,
        "price_usd_cents": 3999,
        "trial_days": 7,
    },
}

PLAN_FEATURE_ROWS: dict[str, dict[str, int | None]] = {
    "free": {
        "daily_rituals": 1,
        "max_goals": 2,
        "max_guidance_modes": 1,
        "daily_readings": 1,
        "history_days": 7,
    },
    "premium_monthly": {
        "daily_rituals": None,
        "max_goals": 13,
        "max_guidance_modes": None,
        "deep_rituals": None,
        "ai_reflection": None,
        "deep_readings": None,
        "history_days": None,
        "streak_freezes_per_month": 2,
        "custom_reminders": None,
        "premium_quests": None,
    },
    "premium_yearly": {
        "daily_rituals": None,
        "max_goals": 13,
        "max_guidance_modes": None,
        "deep_rituals": None,
        "ai_reflection": None,
        "deep_readings": None,
        "history_days": None,
        "streak_freezes_per_month": 2,
        "custom_reminders": None,
        "premium_quests": None,
    },
}


@dataclass(frozen=True)
class SubscriptionRecord:
    user_id: str
    plan_key: str
    status: str
    current_period_end: datetime


class EntitlementRepository(Protocol):
    def get_plan_key(self, user_id: str) -> str: ...

    def get_plan(self, plan_key: str) -> dict[str, Any]: ...

    def get_features(self, plan_key: str) -> dict[str, int | str]: ...


class InMemoryEntitlementRepository:
    """Schema-shaped local repository; it never connects to Supabase."""

    def __init__(
        self,
        subscriptions: list[SubscriptionRecord] | None = None,
        now: datetime | None = None,
    ) -> None:
        self._subscriptions = list(subscriptions or [])
        self._now = now

    def add_subscription(self, subscription: SubscriptionRecord) -> None:
        self._subscriptions.append(subscription)

    def _current_time(self) -> datetime:
        return self._now or datetime.now(timezone.utc)

    def get_plan_key(self, user_id: str) -> str:
        now = self._current_time()
        active = [
            row
            for row in self._subscriptions
            if row.user_id == str(user_id)
            and row.status in {"active", "trialing"}
            and row.current_period_end > now
            and row.plan_key in PLAN_ROWS
        ]
        if not active:
            return "free"
        newest = max(active, key=lambda row: row.current_period_end)
        return newest.plan_key

    def get_plan(self, plan_key: str) -> dict[str, Any]:
        return dict(PLAN_ROWS.get(plan_key, PLAN_ROWS["free"]))

    def get_features(self, plan_key: str) -> dict[str, int | str]:
        rows = PLAN_FEATURE_ROWS.get(plan_key, PLAN_FEATURE_ROWS["free"])
        return {key: "unlimited" if value is None else value for key, value in rows.items()}


class SupabaseEntitlementRepository:
    """Service-role adapter for the live entitlement tables and view."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def get_plan_key(self, user_id: str) -> str:
        result = self.client.table("user_entitlements").select("plan_key").eq("user_id", str(user_id)).limit(1).execute()
        rows = getattr(result, "data", None) or []
        return rows[0].get("plan_key", "free") if rows else "free"

    def get_plan(self, plan_key: str) -> dict[str, Any]:
        result = self.client.table("plans").select("key,name_en,name_ur,billing_interval,price_pkr,price_usd_cents,trial_days").eq("key", plan_key).limit(1).execute()
        rows = getattr(result, "data", None) or []
        return dict(rows[0]) if rows else dict(PLAN_ROWS["free"])

    def get_features(self, plan_key: str) -> dict[str, int | str]:
        result = self.client.table("plan_features").select("feature_key,value_int,value_text").eq("plan_key", plan_key).execute()
        features: dict[str, int | str] = {}
        for row in getattr(result, "data", None) or []:
            value = row.get("value_int")
            if value is None:
                value = row.get("value_text") or "unlimited"
            features[row["feature_key"]] = value
        return features or dict(PLAN_FEATURE_ROWS["free"])


DEFAULT_REPOSITORY: EntitlementRepository = InMemoryEntitlementRepository()


def get_entitlement(
    user_id: str = "demo_free",
    repository: EntitlementRepository | None = None,
) -> dict[str, Any]:
    repo = repository or DEFAULT_REPOSITORY
    plan_key = repo.get_plan_key(str(user_id))
    plan = repo.get_plan(plan_key)
    features = repo.get_features(plan_key)
    return {
        "plan": plan_key,
        "plan_key": plan_key,
        "is_premium": plan_key != "free",
        "label": plan["name_en"],
        "trial_days": plan["trial_days"],
        "limits": features,
        "features": features,
        "user_id": str(user_id),
        "source": "supabase-entitlements-repository" if isinstance(repo, SupabaseEntitlementRepository) else "in-memory-entitlements-repository",
    }
