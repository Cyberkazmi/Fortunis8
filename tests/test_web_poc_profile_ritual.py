from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

WEB_POC = Path(__file__).resolve().parents[1] / "web-poc"
if str(WEB_POC) not in sys.path:
    sys.path.insert(0, str(WEB_POC))

from backend import main  # noqa: E402
from backend.entitlements import InMemoryEntitlementRepository, SubscriptionRecord  # noqa: E402


@pytest.fixture(autouse=True)
def reset_repositories():
    main.profile_repository._profiles.clear()
    main.entitlement_repository = None
    yield
    main.profile_repository._profiles.clear()
    main.entitlement_repository = None


client = TestClient(main.app)


def payload(**overrides):
    value = {
        "user_id": "profile-user",
        "goals": ["study_exams"],
        "belief_mode": "Scientific",
        "rhythm_minutes": 5,
        "language": "en",
    }
    value.update(overrides)
    return value


def test_valid_profile_is_saved_and_gets_catalog_ritual():
    response = client.post("/api/profile", json=payload(optional_readings=True, delivery_time="08:00", timezone="Asia/Karachi"))
    assert response.status_code == 201
    body = response.json()
    assert body["profile"]["belief_mode"] == "Scientific"
    assert body["profile"]["optional_readings"] is True
    assert body["ritual"]["stable_key"] in {"active_recall", "if_then_plan"}
    assert body["ritual"]["action_step"]

    fetched = client.get("/api/profile", params={"user_id": "profile-user"})
    assert fetched.status_code == 200
    assert fetched.json()["profile"]["goals"] == ["study_exams"]


def test_invalid_belief_mode_is_rejected_with_422():
    response = client.post("/api/profile", json=payload(belief_mode="Astrology"))
    assert response.status_code == 422
    assert "belief_mode" in response.text


def test_free_plan_rejects_mixed_ten_minutes_and_more_than_two_goals():
    assert client.post("/api/profile", json=payload(belief_mode="Mixed")).status_code == 422
    assert client.post("/api/profile", json=payload(rhythm_minutes=10)).status_code == 422
    assert client.post("/api/profile", json=payload(goals=["study_exams", "discipline", "confidence"])).status_code == 422


def test_premium_allows_mixed_ten_minutes_and_three_goals():
    now = datetime.now(timezone.utc)
    main.entitlement_repository = InMemoryEntitlementRepository(
        [SubscriptionRecord("premium-user", "premium_monthly", "active", now + timedelta(days=30))]
    )
    response = client.post(
        "/api/profile",
        json=payload(user_id="premium-user", goals=["study_exams", "discipline", "confidence"], belief_mode="Mixed", rhythm_minutes=10),
    )
    assert response.status_code == 201


def test_daily_ritual_is_deterministic_for_user_and_date():
    client.post("/api/profile", json=payload())
    first = client.get("/api/ritual/today", params={"user_id": "profile-user"}).json()["ritual"]
    second = client.get("/api/ritual/today", params={"user_id": "profile-user"}).json()["ritual"]
    assert first == second


def test_unavailable_mode_falls_back_to_practical_same_goal():
    response = client.post("/api/profile", json=payload(goals=["business_wealth"], belief_mode="Mindfulness", rhythm_minutes=5))
    assert response.status_code == 201
    ritual = response.json()["ritual"]
    assert ritual["guidance_mode"] == "practical"
    assert "business_wealth" in ritual["goals"]
    assert ritual["fallback_used"] is True
