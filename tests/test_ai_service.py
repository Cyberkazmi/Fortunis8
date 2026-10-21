from __future__ import annotations

import types

from app.services import ai_service


class _FakeChoice:
    def __init__(self, content: str):
        self.message = types.SimpleNamespace(content=content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


def test_generate_fortune_returns_text(monkeypatch) -> None:
    fake_client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **kwargs: _FakeResponse(
                    "The stars favor steady, patient steps today. "
                    "Your effort will bloom with gentle momentum."
                )
            )
        )
    )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = ai_service.generate_fortune(
        "Give me a hopeful fortune for today.",
        client=fake_client,
    )

    assert isinstance(result, str)
    assert len(result) > 20
