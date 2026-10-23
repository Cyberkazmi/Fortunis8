from __future__ import annotations

import asyncio
from datetime import date, timedelta
from types import SimpleNamespace

from app.config import settings
from app.services import user_service
from app.services.streak_service import apply_daily_reward


class _FakeMessage:
    def __init__(self) -> None:
        self.responses: list[str] = []

    async def reply_text(self, message: str) -> None:
        self.responses.append(message)


class _FakeUpdate:
    def __init__(self) -> None:
        self.effective_user = SimpleNamespace(
            id=777,
            username="streak_seeker",
            first_name="Streak",
            last_name="Seeker",
        )
        self.message = _FakeMessage()


def _profile() -> dict:
    return {
        "telegram_id": "777",
        "diamonds": 0,
        "streak_count": 0,
        "level": 1,
        "local_mode": True,
    }


def test_daily_command_awards_once_and_preserves_local_profile(monkeypatch):
    update = _FakeUpdate()
    context = SimpleNamespace(user_data={})
    profile = _profile()
    persisted_fields: list[dict] = []

    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "SUPABASE_KEY", None)
    monkeypatch.setattr(user_service, "ensure_profile", lambda user: dict(profile))

    def fake_update_profile(user, **fields):
        persisted_fields.append(fields)
        return {"telegram_id": "777", "local_mode": True, **fields}

    monkeypatch.setattr(user_service, "update_profile", fake_update_profile)

    asyncio.run(user_service.daily_reward(update, context))
    asyncio.run(user_service.daily_reward(update, context))

    assert update.message.responses[0].startswith("Daily reward claimed: +10 diamonds.")
    assert update.message.responses[1] == "You already claimed today's Fortunis8 reward."
    assert persisted_fields == [{"diamonds": 10, "streak_count": 1, "level": 1}]
    assert context.user_data["daily_profile"]["diamonds"] == 10


def test_daily_reward_increases_consecutive_streak():
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    result = apply_daily_reward(
        {"diamonds": 10, "streak_count": 1, "level": 1},
        {"last_daily_date": yesterday},
    )

    assert result["reward_earned"] == 15
    assert result["profile"]["diamonds"] == 25
    assert result["profile"]["streak_count"] == 2
    assert result["new_last_daily_date"] == date.today().isoformat()


def test_build_application_registers_daily_reward_aliases(monkeypatch):
    class FakeApplication:
        def __init__(self) -> None:
            self.handlers = []

        def add_handler(self, handler) -> None:
            self.handlers.append(handler)

    application = FakeApplication()

    class FakeBuilder:
        def token(self, token):
            return self

        def build(self):
            return application

    monkeypatch.setattr(settings, "validate", lambda: True)
    monkeypatch.setattr(user_service, "ApplicationBuilder", FakeBuilder)

    user_service.build_application()

    command_sets = [getattr(handler, "commands", set()) for handler in application.handlers]
    assert {"daily"} in command_sets
    assert {"reward"} in command_sets
