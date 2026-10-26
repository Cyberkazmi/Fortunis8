from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WEB_POC = Path(__file__).resolve().parents[1] / "web-poc"
if str(WEB_POC) not in sys.path:
    sys.path.insert(0, str(WEB_POC))

from backend.entitlements import (  # noqa: E402
    InMemoryEntitlementRepository,
    SubscriptionRecord,
    get_entitlement,
)


NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)


def repo(*subscriptions: SubscriptionRecord) -> InMemoryEntitlementRepository:
    return InMemoryEntitlementRepository(list(subscriptions), now=NOW)


def subscription(user_id: str, plan_key: str, status: str, days: int) -> SubscriptionRecord:
    return SubscriptionRecord(user_id, plan_key, status, NOW + timedelta(days=days))


def test_unknown_users_default_to_free():
    result = get_entitlement("new-user", repository=repo())
    assert result["plan"] == "free"
    assert result["is_premium"] is False
    assert result["features"]["max_goals"] == 2


def test_active_monthly_and_yearly_are_schema_plan_keys():
    monthly = get_entitlement("monthly", repository=repo(subscription("monthly", "premium_monthly", "active", 30)))
    yearly = get_entitlement("yearly", repository=repo(subscription("yearly", "premium_yearly", "active", 365)))
    assert monthly["plan"] == "premium_monthly"
    assert yearly["plan"] == "premium_yearly"
    assert monthly["is_premium"] is True


def test_expired_and_canceled_subscriptions_fall_back_to_free():
    repository = repo(
        subscription("expired", "premium_monthly", "active", -1),
        subscription("canceled", "premium_yearly", "cancelled", 365),
    )
    assert get_entitlement("expired", repository=repository)["plan"] == "free"
    assert get_entitlement("canceled", repository=repository)["plan"] == "free"


def test_trialing_subscription_is_premium():
    result = get_entitlement(
        "trial",
        repository=repo(subscription("trial", "premium_monthly", "trialing", 7)),
    )
    assert result["is_premium"] is True
    assert result["trial_days"] == 7


def test_newest_valid_subscription_wins():
    repository = repo(
        subscription("switching", "premium_monthly", "active", 10),
        subscription("switching", "premium_yearly", "active", 365),
    )
    assert get_entitlement("switching", repository=repository)["plan"] == "premium_yearly"


def test_free_and_premium_feature_limits_and_unlimited_values():
    free = get_entitlement("free", repository=repo())
    premium = get_entitlement("premium", repository=repo(subscription("premium", "premium_monthly", "active", 30)))
    assert free["features"]["max_goals"] == 2
    assert premium["features"]["max_goals"] == 13
    assert premium["features"]["daily_rituals"] == "unlimited"
    assert premium["features"]["ai_reflection"] == "unlimited"
