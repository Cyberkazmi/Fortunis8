from __future__ import annotations

import sys
from pathlib import Path

WEB_POC = Path(__file__).resolve().parents[1] / "web-poc"
if str(WEB_POC) not in sys.path:
    sys.path.insert(0, str(WEB_POC))

from backend.entitlements import get_entitlement  # noqa: E402


def test_unknown_users_default_to_free_entitlement():
    result = get_entitlement("new-user")

    assert result["is_premium"] is False
    assert result["plan"] == "free"
    assert result["limits"]["max_goals"] == 2


def test_stub_premium_entitlement_exposes_premium_limits():
    result = get_entitlement("demo_premium")

    assert result["is_premium"] is True
    assert result["plan"] == "premium"
    assert result["trial_days"] == 7
    assert result["limits"]["history_days"] == "full"


def test_requested_plan_is_explicit_and_does_not_require_payment():
    result = get_entitlement("demo_free", requested_plan="premium")

    assert result["is_premium"] is True
    assert result["source"] == "plans/entitlements-stub"
