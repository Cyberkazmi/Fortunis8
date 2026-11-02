from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

WEB_POC = Path(__file__).resolve().parents[1] / "web-poc"
if str(WEB_POC) not in sys.path:
    sys.path.insert(0, str(WEB_POC))

from backend import auth, main  # noqa: E402
from backend.entitlements import InMemoryEntitlementRepository, SubscriptionRecord  # noqa: E402
from backend.profile_service import ProfileRepository  # noqa: E402


SECRET = "test-secret-for-fortunis8"
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_repositories():
    main.profile_repository = ProfileRepository()
    main.entitlement_repository = None
    main.completion_repository.clear()
    auth.token_verifier = auth.SupabaseJWTVerifier(SECRET, audience="authenticated")
    yield
    main.profile_repository = ProfileRepository()
    main.entitlement_repository = None
    main.completion_repository.clear()


def token(user_id: str, expires_in: int = 3600) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "aud": "authenticated",
            "role": "authenticated",
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        },
        SECRET,
        algorithm="HS256",
    )


def headers(user_id: str = "profile-user") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(user_id)}"}


def payload(**overrides):
    value = {
        "goals": ["study_exams"],
        "belief_mode": "Scientific",
        "rhythm_minutes": 5,
        "language": "en",
        "optional_readings": False,
        "preferred_delivery_window": "morning",
        "notification_frequency": "daily",
        "notifications_enabled": True,
    }
    value.update(overrides)
    return value


def test_missing_authentication_is_rejected():
    response = client.get("/api/profile/me")
    assert response.status_code == 401
    assert "Bearer" in response.headers["www-authenticate"]


def test_invalid_and_expired_tokens_are_rejected():
    invalid = client.get("/api/profile/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert invalid.status_code == 401
    expired = client.get("/api/profile/me", headers={"Authorization": f"Bearer {token('expired', -1)}"})
    assert expired.status_code == 401


def test_valid_profile_is_persisted_and_gets_catalog_ritual():
    response = client.put("/api/profile/me", headers=headers(), json=payload(optional_readings=True, timezone="Asia/Karachi"))
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["user_id"] == "profile-user"
    assert body["profile"]["belief_mode"] == "Scientific"
    assert body["profile"]["optional_readings"] is True
    assert body["ritual"]["action_step"]

    fetched = client.get("/api/profile/me", headers=headers())
    assert fetched.status_code == 200
    assert fetched.json()["profile"]["goals"] == ["study_exams"]


def test_profile_update_replaces_owned_preferences():
    client.put("/api/profile/me", headers=headers(), json=payload())
    response = client.put(
        "/api/profile/me",
        headers=headers(),
        json=payload(goals=["discipline"], belief_mode="Practical", rhythm_minutes=2, language="ur"),
    )
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["goals"] == ["discipline"]
    assert profile["belief_mode"] == "Practical"
    assert profile["language"] == "ur"


def test_cross_user_access_is_denied_by_authenticated_identity():
    created = client.put("/api/profile/me", headers=headers("user-a"), json=payload())
    assert created.status_code == 200
    other = client.get("/api/profile/me", headers=headers("user-b"))
    assert other.status_code == 404
    attempted_impersonation = client.put(
        "/api/profile/me",
        headers=headers("user-b"),
        json={**payload(), "user_id": "user-a"},
    )
    assert attempted_impersonation.status_code == 200
    assert attempted_impersonation.json()["profile"]["user_id"] == "user-b"


def test_invalid_profile_values_are_rejected_with_422():
    assert client.put("/api/profile/me", headers=headers(), json=payload(belief_mode="Astrology")).status_code == 422
    assert client.put("/api/profile/me", headers=headers(), json=payload(rhythm_minutes=7)).status_code == 422
    assert client.put("/api/profile/me", headers=headers(), json=payload(goals=["not_a_goal"])).status_code == 422


def test_free_plan_rejects_mixed_ten_minutes_and_more_than_two_goals():
    assert client.put("/api/profile/me", headers=headers(), json=payload(belief_mode="Mixed")).status_code == 422
    assert client.put("/api/profile/me", headers=headers(), json=payload(rhythm_minutes=10)).status_code == 422
    assert client.put(
        "/api/profile/me",
        headers=headers(),
        json=payload(goals=["study_exams", "discipline", "confidence"]),
    ).status_code == 422


def test_premium_allows_mixed_ten_minutes_and_three_goals():
    now = datetime.now(timezone.utc)
    main.entitlement_repository = InMemoryEntitlementRepository(
        [SubscriptionRecord("premium-user", "premium_monthly", "active", now + timedelta(days=30))]
    )
    response = client.put(
        "/api/profile/me",
        headers=headers("premium-user"),
        json=payload(user_id="ignored", goals=["study_exams", "discipline", "confidence"], belief_mode="Mixed", rhythm_minutes=10),
    )
    assert response.status_code == 200
    assert response.json()["profile"]["user_id"] == "premium-user"


def test_daily_ritual_is_deterministic_for_authenticated_user():
    client.put("/api/profile/me", headers=headers(), json=payload())
    first = client.get("/api/ritual/today", headers=headers()).json()["ritual"]
    second = client.get("/api/ritual/today", headers=headers()).json()["ritual"]
    assert first == second


def test_ritual_requires_an_existing_owned_profile():
    response = client.get("/api/ritual/today", headers=headers("missing-user"))
    assert response.status_code == 404


def test_entitlement_me_uses_authenticated_identity():
    response = client.get("/api/entitlement/me", headers=headers("entitled-user"))
    assert response.status_code == 200
    assert response.json()["user_id"] == "entitled-user"
    assert response.json()["plan"] == "free"


def test_ritual_completion_is_server_rewarded_and_idempotent():
    client.put("/api/profile/me", headers=headers(), json=payload())
    ritual = client.get("/api/ritual/today", headers=headers()).json()["ritual"]
    first = client.post("/api/ritual-completions", headers=headers(), json={"stable_key": ritual["stable_key"]})
    second = client.post("/api/ritual-completions", headers=headers(), json={"stable_key": ritual["stable_key"]})
    assert first.status_code == 200
    assert first.json()["xp_awarded"] == 40
    assert first.json()["diamonds_awarded"] == 20
    assert second.status_code == 200
    assert second.json()["already_completed"] is True
    assert second.json()["xp_awarded"] == 0


def test_ritual_completion_cannot_claim_another_assignment():
    client.put("/api/profile/me", headers=headers(), json=payload())
    response = client.post("/api/ritual-completions", headers=headers(), json={"stable_key": "not-assigned"})
    assert response.status_code == 403
