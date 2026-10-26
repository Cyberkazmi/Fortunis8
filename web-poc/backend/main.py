from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.entitlements import EntitlementRepository, get_entitlement
from backend.profile_service import (
    BELIEF_MODES,
    GOALS,
    RHYTHMS,
    ProfileRepository,
    UserProfile,
    choose_ritual,
)

app = FastAPI(title="Fortunis8 Hybrid POC")
profile_repository = ProfileRepository()
entitlement_repository: EntitlementRepository | None = None


class ProfilePayload(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    goals: list[str] = Field(min_length=1, max_length=13)
    belief_mode: str
    rhythm_minutes: int
    language: Literal["en", "ur"] = "en"
    optional_readings: bool = False
    delivery_time: str | None = None
    timezone: str | None = None

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
            raise ValueError("belief_mode must be one of Scientific, Mindfulness, Spiritual, Religious, Practical, Mixed")
        return value

    @field_validator("rhythm_minutes")
    @classmethod
    def validate_rhythm(cls, value: int) -> int:
        if value not in RHYTHMS:
            raise ValueError("rhythm_minutes must be 2, 5, or 10")
        return value


def _entitlement(user_id: str) -> dict:
    return get_entitlement(user_id, repository=entitlement_repository)


def _validate_entitled_profile(payload: ProfilePayload) -> None:
    entitlement = _entitlement(payload.user_id)
    limits = entitlement["limits"]
    max_goals = limits.get("max_goals", 2)
    if isinstance(max_goals, int) and len(payload.goals) > max_goals:
        raise HTTPException(status_code=422, detail=f"Your plan allows up to {max_goals} goals.")
    if payload.belief_mode == "Mixed" and entitlement["plan"] == "free":
        raise HTTPException(status_code=422, detail="Mixed guidance mode requires Premium.")
    if payload.rhythm_minutes == 10 and entitlement["plan"] == "free":
        raise HTTPException(status_code=422, detail="10-minute rituals require Premium.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "FastAPI backend is online."}


@app.get("/api/entitlement")
def entitlement(user_id: str = "demo_free") -> dict:
    return _entitlement(user_id)


@app.post("/api/profile", status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfilePayload) -> dict:
    _validate_entitled_profile(payload)
    profile = profile_repository.save(
        UserProfile(
            user_id=payload.user_id,
            goals=tuple(payload.goals),
            belief_mode=payload.belief_mode,
            rhythm_minutes=payload.rhythm_minutes,
            language=payload.language,
            optional_readings=payload.optional_readings,
            delivery_time=payload.delivery_time,
            timezone=payload.timezone,
        )
    )
    return {"profile": profile_to_dict(profile), "ritual": choose_ritual(profile, profile.user_id)}


@app.get("/api/profile")
def get_profile(user_id: str = Query(min_length=1, max_length=128)) -> dict:
    profile = profile_repository.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile_to_dict(profile)}


@app.get("/api/ritual/today")
def ritual_today(user_id: str = Query(min_length=1, max_length=128)) -> dict:
    profile = profile_repository.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile_to_dict(profile), "ritual": choose_ritual(profile, user_id)}


def profile_to_dict(profile: UserProfile) -> dict:
    return {
        "user_id": profile.user_id,
        "goals": list(profile.goals),
        "belief_mode": profile.belief_mode,
        "rhythm_minutes": profile.rhythm_minutes,
        "language": profile.language,
        "optional_readings": profile.optional_readings,
        "delivery_time": profile.delivery_time,
        "timezone": profile.timezone,
    }


frontend_dir = Path(__file__).resolve().parent.parent / "dist"
index_file = frontend_dir / "index.html"


@app.get("/dashboard", include_in_schema=False)
@app.get("/onboarding", include_in_schema=False)
@app.get("/reading/tarot", include_in_schema=False)
@app.get("/technical-poc", include_in_schema=False)
def preview_page() -> FileResponse:
    return FileResponse(index_file)


if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
