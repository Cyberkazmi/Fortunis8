from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

WEB_POC = Path(__file__).resolve().parents[1] / "web-poc"
if str(WEB_POC) not in sys.path:
    sys.path.insert(0, str(WEB_POC))

from backend import ai_ritual_service as ai  # noqa: E402
from backend.profile_service import UserProfile  # noqa: E402


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    ai.clear_cache()
    monkeypatch.setenv("FORTUNIS8_AI_MODE", "live")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("FORTUNIS8_AI_MODEL", "gpt-5-nano")
    yield
    ai.clear_cache()


def profile() -> UserProfile:
    return UserProfile(
        user_id="ai-user",
        goals=("study_exams",),
        belief_mode="Scientific",
        rhythm_minutes=5,
        language="en",
        optional_readings=True,
        current_state="focused",
    )


def test_strict_json_request_uses_goal_mode_language_and_schema(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": json.dumps({
                    "title": "One focused study sprint",
                    "description": "Choose one topic and make the first step visible.",
                    "guidance_mode": "scientific",
                    "duration_minutes": 5,
                    "ritual_steps": ["Choose one topic", "Set a five-minute timer"],
                    "action_step": "Complete the first five-minute block.",
                    "tarot_reflection": {
                        "card_name": "The Magician",
                        "interpretation": "Notice which tool or skill is already available to you.",
                        "reflection_question": "What can you begin with what you already have?",
                    },
                    "safety_note": "Symbolic reflection only; it does not guarantee an outcome.",
                })}}]
            }

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(ai.httpx, "post", fake_post)
    result = ai.generate_experience(profile(), "ai-user")

    assert result["source"] == "openai-strict-json"
    assert result["tarot_reflection"]["card_name"] == "The Magician"
    payload = calls[0][1]["json"]
    assert payload["model"] == "gpt-5-nano"
    assert payload["response_format"]["json_schema"]["strict"] is True
    user_prompt = payload["messages"][1]["content"]
    assert "study_exams" in user_prompt
    assert "Scientific" in user_prompt
    assert "English" in user_prompt


def test_invalid_ai_json_uses_safe_catalog_fallback(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": '{"not": "the contract"}'}}]}

    monkeypatch.setattr(ai.httpx, "post", lambda *args, **kwargs: Response())
    result = ai.generate_experience(profile(), "ai-user")
    assert result["source"] == "catalog-fallback"
    assert result["fallback_used"] is True
    assert result["tarot_reflection"]["reflection_question"]


def test_live_result_is_cached_for_same_user_and_date(monkeypatch):
    count = 0

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": json.dumps({
                    "title": "A calm start",
                    "description": "Begin with one clear action.",
                    "guidance_mode": "scientific",
                    "duration_minutes": 5,
                    "ritual_steps": ["Name the task", "Start for five minutes"],
                    "action_step": "Start the timer now.",
                    "tarot_reflection": {
                        "card_name": "The Star",
                        "interpretation": "Let a small signal guide your attention.",
                        "reflection_question": "What would make progress visible today?",
                    },
                    "safety_note": "Reflective prompt only; no prediction is intended.",
                })}}]
            }

    def fake_post(*args, **kwargs):
        nonlocal count
        count += 1
        return Response()

    monkeypatch.setattr(ai.httpx, "post", fake_post)
    first = ai.generate_experience(profile(), "ai-user")
    second = ai.generate_experience(profile(), "ai-user")
    assert first == second
    assert count == 1
