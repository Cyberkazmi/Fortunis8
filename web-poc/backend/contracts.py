from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.profile_service import BELIEF_MODES, GOALS, RHYTHMS


class ProfilePayload(BaseModel):
    goals: list[str] = Field(min_length=1, max_length=13)
    belief_mode: str
    rhythm_minutes: int
    language: Literal["en", "ur"] = "en"
    optional_readings: bool = False
    delivery_time: str | None = None
    timezone: str | None = None
    current_state: str | None = None
    preferred_delivery_window: str = "morning"
    notification_frequency: Literal["daily", "weekdays", "manual"] = "daily"
    notifications_enabled: bool = True

    @field_validator("goals")
    @classmethod
    def validate_goals(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values) or any(goal not in GOALS for goal in values):
            raise ValueError("goals must be unique catalog goal keys")
        return values

    @field_validator("belief_mode")
    @classmethod
    def validate_belief_mode(cls, value: str) -> str:
        if value not in BELIEF_MODES:
            raise ValueError(
                "belief_mode must be one of Scientific, Mindfulness, Spiritual, Religious, Practical, Mixed"
            )
        return value

    @field_validator("rhythm_minutes")
    @classmethod
    def validate_rhythm(cls, value: int) -> int:
        if value not in RHYTHMS:
            raise ValueError("rhythm_minutes must be 2, 5, or 10")
        return value

    @field_validator("preferred_delivery_window")
    @classmethod
    def validate_delivery_window(cls, value: str) -> str:
        if value not in {"morning", "afternoon", "evening", "flexible"}:
            raise ValueError("preferred_delivery_window must be morning, afternoon, evening, or flexible")
        return value


class RitualResponse(BaseModel):
    stable_key: str
    title: str
    description: str
    guidance_mode: str
    duration_minutes: int
    goals: list[str]
    action_step: str
    fallback_used: bool
    date: str


class ProfileResponse(BaseModel):
    user_id: str
    goals: list[str]
    belief_mode: str
    rhythm_minutes: int
    language: Literal["en", "ur"]
    optional_readings: bool
    delivery_time: str | None
    timezone: str | None
    current_state: str | None
    preferred_delivery_window: str
    notification_frequency: str
    notifications_enabled: bool


class ProfileEnvelope(BaseModel):
    profile: ProfileResponse


class ProfileWithRitualEnvelope(ProfileEnvelope):
    ritual: RitualResponse


class EntitlementResponse(BaseModel):
    plan: str
    plan_key: str
    is_premium: bool
    label: str
    trial_days: int
    limits: dict[str, int | str]
    features: dict[str, int | str]
    user_id: str
    source: str


class RitualCompletionPayload(BaseModel):
    stable_key: str = Field(min_length=1, max_length=120)


class RitualCompletionResponse(BaseModel):
    stable_key: str
    completed_for: str
    already_completed: bool
    xp_awarded: int
    diamonds_awarded: int
