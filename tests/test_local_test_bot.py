from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.bot import local_test_bot


class FakeMessage:
    def __init__(self) -> None:
        self.responses: list[str] = []
        self.edits: list[str] = []

    async def reply_text(self, message: str, **kwargs) -> None:
        self.responses.append(message)

    async def edit_text(self, message: str, **kwargs) -> None:
        self.edits.append(message)


class FakeQuery:
    def __init__(self, data: str, message: FakeMessage) -> None:
        self.data = data
        self.message = message
        self.answers = 0

    async def answer(self) -> None:
        self.answers += 1

    async def edit_message_text(self, message: str, **kwargs) -> None:
        await self.message.edit_text(message, **kwargs)


class FakeUpdate:
    def __init__(self, data: str | None = None) -> None:
        self.effective_user = SimpleNamespace(id=77)
        self.message = FakeMessage()
        self.callback_query = FakeQuery(data, self.message) if data else None


def callback(data: str, context: SimpleNamespace, message: FakeMessage) -> None:
    update = FakeUpdate(data)
    update.callback_query.message = message
    asyncio.run(local_test_bot.callback(update, context))


def test_local_start_to_first_ritual_uses_selected_buttons_only():
    store = local_test_bot.InMemoryTestProfileRepository()
    context = SimpleNamespace(user_data={}, bot_data={"profile_store": store})
    update = FakeUpdate()

    asyncio.run(local_test_bot.start(update, context))
    callback("test:goal:study_exams", context, update.message)
    callback("test:belief:scientific", context, update.message)
    callback("test:rhythm:5", context, update.message)

    profile = store.get(77)
    assert profile is not None
    assert profile.goal == "study_exams"
    assert profile.belief_mode == "scientific"
    assert profile.rhythm_minutes == 5
    assert "first ritual is ready" in update.message.edits[-1]


def test_local_builder_requires_environment_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        local_test_bot.build_test_application()


def test_local_builder_reads_token_and_registers_polling_flow(monkeypatch):
    built = SimpleNamespace(bot_data={}, handlers=[])

    class FakeBuilder:
        def token(self, token):
            assert token == "test-only-token"
            return self

        def build(self):
            return built

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-only-token")
    monkeypatch.setattr(local_test_bot, "ApplicationBuilder", FakeBuilder)
    monkeypatch.setattr(built, "add_handler", lambda handler: built.handlers.append(handler), raising=False)

    result = local_test_bot.build_test_application()

    assert result is built
    assert len(result.handlers) == 1
    assert result.bot_data["profile_store"].profiles == {}
