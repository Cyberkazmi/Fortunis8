from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.config import settings
from app.services import quest_service, user_service


class _FakeMessage:
    def __init__(self) -> None:
        self.responses: list[str] = []

    async def reply_text(self, message: str) -> None:
        self.responses.append(message)


class _FakeUpdate:
    def __init__(self, user) -> None:
        self.effective_user = user
        self.message = _FakeMessage()


def _fake_user():
    return SimpleNamespace(
        id=12345,
        username="quest_seeker",
        first_name="Quest",
        last_name="Seeker",
    )


def test_quest_service_imports_and_completes_local_quest(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "SUPABASE_KEY", None)
    quest_service.LOCAL_QUESTS.clear()
    user = _fake_user()

    try:
        result = quest_service.complete_quest(user, "daily_fortune")

        assert result["completed"] is True
        assert result["reward_diamonds"] == 25
        assert result["profile"]["diamonds"] == 25
        assert result["profile"]["level"] == 1

        repeated = quest_service.complete_quest(user, "daily_fortune")
        assert repeated["completed"] is False
    finally:
        quest_service.LOCAL_QUESTS.clear()


def test_quests_handler_returns_summary(monkeypatch):
    update = _FakeUpdate(_fake_user())
    monkeypatch.setattr(user_service, "get_quest_summary", lambda user: "Your current quests:")

    asyncio.run(user_service.quests(update, SimpleNamespace()))

    assert update.message.responses == ["Your current quests:"]


def test_build_application_registers_quests_command(monkeypatch):
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

    assert any(getattr(handler, "commands", set()) == {"quests"} for handler in application.handlers)
