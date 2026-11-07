from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.services import path_service, user_service


class _FakeMessage:
    def __init__(self) -> None:
        self.responses: list[str] = []
        self.edits: list[str] = []

    async def reply_text(self, message: str, **kwargs) -> None:
        self.responses.append(message)

    async def edit_text(self, message: str, **kwargs) -> None:
        self.edits.append(message)


class _FakeQuery:
    def __init__(self, data: str, message: _FakeMessage) -> None:
        self.data = data
        self.message = message
        self.answers = 0

    async def answer(self) -> None:
        self.answers += 1

    async def edit_message_text(self, message: str, **kwargs) -> None:
        await self.message.edit_text(message, **kwargs)


class _FakeUpdate:
    def __init__(self, data: str | None = None) -> None:
        self.effective_user = SimpleNamespace(id=4242, first_name="Path", username="path_user")
        self.message = _FakeMessage()
        self.callback_query = _FakeQuery(data, self.message) if data else None


def _callback(data: str, context: SimpleNamespace, message: _FakeMessage) -> None:
    update = _FakeUpdate(data)
    update.callback_query.message = message
    asyncio.run(path_service.path_callback(update, context))


def test_button_onboarding_builds_path_and_initializes_quests():
    context = SimpleNamespace(user_data={})
    update = _FakeUpdate()

    asyncio.run(path_service.path_onboarding(update, context))
    assert "Build your Fortunis8 daily path" in update.message.responses[0]

    _callback("path:welcome", context, update.message)
    _callback("path:goal:study_exams", context, update.message)
    _callback("path:goals_next", context, update.message)
    _callback("path:mode:scientific", context, update.message)
    _callback("path:state:motivated", context, update.message)
    _callback("path:duration:5", context, update.message)
    _callback("path:window:morning", context, update.message)
    _callback("path:confirm", context, update.message)

    assert context.user_data["path_profile"]["goals"] == ["study_exams"]
    assert context.user_data["path_profile"]["guidance_mode"] == "scientific"
    assert context.user_data["path_profile"]["current_state"] == "motivated"
    assert context.user_data["path_quests"]["level"] == 1
    assert any("Your first quests are ready" in message for message in update.message.edits)


def test_path_quest_completion_awards_xp_diamonds_and_streak():
    context = SimpleNamespace(
        user_data={
            "path_profile": {"goals": ["study_exams"]},
            "path_quests": path_service.new_progression(),
        },
        args=["daily_ritual"],
    )
    update = _FakeUpdate()

    asyncio.run(path_service.complete_path_quest(update, context))

    state = context.user_data["path_quests"]
    assert state["xp"] == 40
    assert state["diamonds"] == 10
    assert state["streak"] == 1
    assert "Quest complete" in update.message.responses[0]


def test_user_service_registers_path_commands(monkeypatch):
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

    from app.config import settings

    monkeypatch.setattr(settings, "validate", lambda: True)
    monkeypatch.setattr(user_service, "ApplicationBuilder", FakeBuilder)

    user_service.build_application()

    command_sets = [getattr(handler, "commands", set()) for handler in application.handlers]
    assert {"quests"} in command_sets
    assert {"done"} in command_sets
    path_conversation = application.handlers[0]
    assert {"path", "onboard"} == {command for entry in path_conversation.entry_points for command in entry.commands}
