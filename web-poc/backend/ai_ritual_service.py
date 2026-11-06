from __future__ import annotations

from datetime import date
import hashlib
import json
import os
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.profile_service import UserProfile, choose_ritual


class TarotReflection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card_name: str = Field(min_length=1, max_length=80)
    interpretation: str = Field(min_length=1, max_length=900)
    reflection_question: str = Field(min_length=1, max_length=300)


class GeneratedExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=900)
    guidance_mode: str = Field(min_length=1, max_length=40)
    duration_minutes: int = Field(ge=2, le=10)
    ritual_steps: list[str] = Field(min_length=2, max_length=4)
    action_step: str = Field(min_length=1, max_length=300)
    tarot_reflection: TarotReflection
    safety_note: str = Field(min_length=1, max_length=300)


ALLOWED_GUIDANCE_MODES = {
    "scientific",
    "mindfulness",
    "spiritual_reflection",
    "religious_practice",
    "practical",
    "mixed",
    "motivational",
    "visualization",
}

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "guidance_mode": {"type": "string"},
        "duration_minutes": {"type": "integer"},
        "ritual_steps": {
            "type": "array",
            "items": {"type": "string"},
        },
        "action_step": {"type": "string"},
        "tarot_reflection": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "card_name": {"type": "string"},
                "interpretation": {"type": "string"},
                "reflection_question": {"type": "string"},
            },
            "required": ["card_name", "interpretation", "reflection_question"],
        },
        "safety_note": {"type": "string"},
    },
    "required": [
        "title",
        "description",
        "guidance_mode",
        "duration_minutes",
        "ritual_steps",
        "action_step",
        "tarot_reflection",
        "safety_note",
    ],
}

_SYSTEM_PROMPT = """You are Fortunis8's daily growth guide. Generate one small, practical ritual and one optional tarot-style reflection prompt.

Rules:
- Return only the JSON object required by the schema. Never use Markdown or add keys.
- Use the user's selected goal, belief mode, and language. Never infer a belief system.
- The ritual must fit the requested duration and end with one concrete action step.
- Use evidence-informed habit, attention, reflection, planning, or implementation-intention ideas where useful.
- The tarot section is symbolic reflection only. It must not predict events, claim supernatural certainty, or guarantee wealth, health, relationships, employment, grades, or other outcomes.
- Do not diagnose, prescribe treatment, or make medical or psychological guarantees.
- Keep the tone warm, clear, and actionable. Honor Religious or Spiritual modes without asserting doctrine.
- The safety_note must state that the reading is reflective and not a guarantee when the tarot prompt is used.
"""

_CACHE: dict[tuple[str, str], dict[str, Any]] = {}


def _live_mode() -> bool:
    return os.getenv("FORTUNIS8_AI_MODE", "off").lower() == "live" and bool(os.getenv("OPENAI_API_KEY"))


def _prompt(profile: UserProfile) -> str:
    goals = ", ".join(profile.goals)
    language_name = "Urdu" if profile.language == "ur" else "English"
    current_state = profile.current_state or "not specified"
    return (
        f"Goal(s): {goals}\n"
        f"Belief mode selected by user: {profile.belief_mode}\n"
        f"Language: {language_name}\n"
        f"Maximum ritual duration: {profile.rhythm_minutes} minutes\n"
        f"Current state selected by user: {current_state}\n"
        "Generate exactly one daily ritual and one optional symbolic tarot reflection."
    )


def _call_llm(profile: UserProfile) -> GeneratedExperience:
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    endpoint = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    payload = {
        "model": os.getenv("FORTUNIS8_AI_MODEL", "gpt-5-nano"),
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _prompt(profile)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "fortunis8_daily_growth_experience",
                "strict": True,
                "schema": _SCHEMA,
            },
        },
        "reasoning": {"effort": "minimal"},
        "max_completion_tokens": 1400,
    }
    response = httpx.post(
        endpoint,
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"},
        json=payload,
        timeout=35.0,
    )
    response.raise_for_status()
    body = response.json()
    try:
        content = body["choices"][0]["message"]["content"]
        raw = json.loads(content)
        if isinstance(raw, dict) and isinstance(raw.get("ritual_steps"), list) and len(raw["ritual_steps"]) > 4:
            raw["ritual_steps"] = [*raw["ritual_steps"][:3], raw.get("action_step", "")]
        parsed = GeneratedExperience.model_validate(raw)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("The AI response did not match the Fortunis8 JSON contract.") from exc
    if parsed.guidance_mode.lower() not in ALLOWED_GUIDANCE_MODES:
        raise ValueError("The AI response used an unsupported guidance mode.")
    if parsed.duration_minutes not in {2, 5, 10}:
        raise ValueError("The AI response used an unsupported ritual duration.")
    if parsed.duration_minutes > profile.rhythm_minutes:
        raise ValueError("The AI response exceeded the user's selected ritual duration.")
    return parsed


def _fallback(profile: UserProfile, user_id: str, on_date: date) -> dict[str, Any]:
    ritual = choose_ritual(profile, user_id, on_date)
    return {
        **ritual,
        "fallback_used": True,
        "source": "catalog-fallback",
        "tarot_reflection": {
            "card_name": "The Next Step",
            "interpretation": "Use this symbolic prompt to notice one useful action without treating it as a prediction.",
            "reflection_question": "What small action would make your chosen direction visible today?",
        },
        "safety_note": "Reflection prompt only; it does not predict outcomes or guarantee results.",
    }


def generate_experience(profile: UserProfile, user_id: str, on_date: date | None = None) -> dict[str, Any]:
    day = on_date or date.today()
    key = (str(user_id), day.isoformat())
    if key in _CACHE:
        return dict(_CACHE[key])
    if _live_mode():
        try:
            generated = _call_llm(profile)
            digest = hashlib.sha256(f"ai:{user_id}:{day.isoformat()}".encode()).hexdigest()[:16]
            result = {
                "stable_key": f"ai_{digest}",
                "title": generated.title,
                "description": generated.description,
                "guidance_mode": generated.guidance_mode.lower(),
                "duration_minutes": generated.duration_minutes,
                "goals": list(profile.goals),
                "action_step": generated.action_step,
                "fallback_used": False,
                "date": day.isoformat(),
                "source": "openai-strict-json",
                "ritual_steps": generated.ritual_steps,
                "tarot_reflection": generated.tarot_reflection.model_dump(),
                "safety_note": generated.safety_note,
            }
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            if os.getenv("FORTUNIS8_AI_FAIL_CLOSED", "false").lower() == "true":
                raise RuntimeError("AI ritual generation is unavailable and fail-closed mode is enabled.") from exc
            result = _fallback(profile, user_id, day)
            result["ai_error"] = "AI generation unavailable; safe catalog fallback used."
    else:
        result = _fallback(profile, user_id, day)
    _CACHE[key] = dict(result)
    return result


def clear_cache() -> None:
    _CACHE.clear()
