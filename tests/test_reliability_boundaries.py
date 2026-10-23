from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.api.routes import ready
from app.config import settings
from app.services import user_service


class _FakeMessage:
    def __init__(self) -> None:
        self.responses: list[str] = []

    async def reply_text(self, message: str) -> None:
        self.responses.append(message)


class _FakeUpdate:
    def __init__(self) -> None:
        self.effective_user = SimpleNamespace(
            id=42,
            username="reader",
            first_name="Reader",
            last_name=None,
        )
        self.message = _FakeMessage()


def test_ready_reports_missing_telegram_configuration(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    result = asyncio.run(ready())

    assert result == {"status": "not_ready", "missing": ["TELEGRAM_BOT_TOKEN"]}


def test_ready_reports_ready_with_telegram_configuration(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-token")

    result = asyncio.run(ready())

    assert result == {"status": "ready"}


def test_fortune_handler_returns_fallback_when_ai_fails(monkeypatch):
    update = _FakeUpdate()
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "SUPABASE_KEY", None)
    monkeypatch.setattr(user_service, "generate_horoscope", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))

    asyncio.run(user_service.fortune(update, SimpleNamespace()))

    assert "trouble reaching the reading service" in update.message.responses[0]
