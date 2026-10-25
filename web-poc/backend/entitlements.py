from __future__ import annotations

from typing import Any


PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "plan": "free",
        "is_premium": False,
        "label": "Free",
        "trial_days": 0,
        "limits": {
            "ritual_minutes": [2, 5],
            "max_goals": 2,
            "guidance_modes": 1,
            "readings_per_day": 1,
            "history_days": 7,
        },
    },
    "premium": {
        "plan": "premium",
        "is_premium": True,
        "label": "Premium",
        "trial_days": 7,
        "limits": {
            "ritual_minutes": [2, 5, 10],
            "max_goals": 13,
            "guidance_modes": "mixed",
            "readings_per_day": "unlimited",
            "history_days": "full",
        },
    },
}

# Prototype-only lookup. Replace with Hark's subscription/entitlement tables later.
ENTITLEMENT_STUB = {
    "demo_free": "free",
    "demo_premium": "premium",
}


def get_entitlement(user_id: str = "demo_free", requested_plan: str | None = None) -> dict[str, Any]:
    plan_key = requested_plan or ENTITLEMENT_STUB.get(str(user_id), "free")
    plan = PLANS.get(plan_key, PLANS["free"])
    return {**plan, "user_id": str(user_id), "source": "plans/entitlements-stub"}
