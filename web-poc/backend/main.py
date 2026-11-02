from __future__ import annotations

from pathlib import Path
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.auth import AuthenticatedUser, get_current_user
from backend.contracts import (
    EntitlementResponse,
    ProfileEnvelope,
    ProfilePayload,
    ProfileResponse,
    ProfileWithRitualEnvelope,
    RitualCompletionPayload,
    RitualCompletionResponse,
    RitualResponse,
)
from backend.completion_service import InMemoryCompletionRepository
from backend.entitlements import EntitlementRepository, get_entitlement
from backend.profile_repository import SupabaseProfileRepository
from backend.profile_service import (
    ProfileRepository,
    UserProfile,
    choose_ritual,
)


app = FastAPI(title="Fortunis8 Authenticated MVP API", version="0.2.0")


def _build_profile_repository() -> Any:
    if os.getenv("WEB_POC_PROFILE_REPOSITORY", "memory").lower() != "supabase":
        return ProfileRepository()
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        raise RuntimeError(
            "WEB_POC_PROFILE_REPOSITORY=supabase requires SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY."
        )
    from supabase import create_client

    return SupabaseProfileRepository(create_client(url, service_key))


profile_repository = _build_profile_repository()
entitlement_repository: EntitlementRepository | None = None
completion_repository = InMemoryCompletionRepository()


def _entitlement(user_id: str) -> dict[str, Any]:
    return get_entitlement(user_id, repository=entitlement_repository)


def _validate_entitled_profile(user_id: str, payload: ProfilePayload) -> None:
    entitlement = _entitlement(user_id)
    limits = entitlement["limits"]
    max_goals = limits.get("max_goals", 2)
    if isinstance(max_goals, int) and len(payload.goals) > max_goals:
        raise HTTPException(status_code=422, detail=f"Your plan allows up to {max_goals} goals.")
    if payload.belief_mode == "Mixed" and entitlement["plan"] == "free":
        raise HTTPException(status_code=422, detail="Mixed guidance mode requires Premium.")
    if payload.rhythm_minutes == 10 and entitlement["plan"] == "free":
        raise HTTPException(status_code=422, detail="10-minute rituals require Premium.")


def profile_to_dict(profile: UserProfile) -> dict[str, Any]:
    return {
        "user_id": profile.user_id,
        "goals": list(profile.goals),
        "belief_mode": profile.belief_mode,
        "rhythm_minutes": profile.rhythm_minutes,
        "language": profile.language,
        "optional_readings": profile.optional_readings,
        "delivery_time": profile.delivery_time,
        "timezone": profile.timezone,
        "current_state": profile.current_state,
        "preferred_delivery_window": profile.preferred_delivery_window,
        "notification_frequency": profile.notification_frequency,
        "notifications_enabled": profile.notifications_enabled,
    }


def _profile_or_404(user_id: str) -> UserProfile:
    profile = profile_repository.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.get("/health", response_model=dict[str, str])
def health() -> dict[str, str]:
    return {"status": "ok", "message": "FastAPI backend is online."}


@app.get("/api/profile/me", response_model=ProfileEnvelope)
def get_my_profile(current_user: AuthenticatedUser = Depends(get_current_user)) -> ProfileEnvelope:
    profile = _profile_or_404(current_user.user_id)
    return ProfileEnvelope(profile=ProfileResponse(**profile_to_dict(profile)))


@app.put("/api/profile/me", response_model=ProfileWithRitualEnvelope, status_code=status.HTTP_200_OK)
def save_my_profile(
    payload: ProfilePayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProfileWithRitualEnvelope:
    _validate_entitled_profile(current_user.user_id, payload)
    profile = profile_repository.save(
        UserProfile(
            user_id=current_user.user_id,
            goals=tuple(payload.goals),
            belief_mode=payload.belief_mode,
            rhythm_minutes=payload.rhythm_minutes,
            language=payload.language,
            optional_readings=payload.optional_readings,
            delivery_time=payload.delivery_time,
            timezone=payload.timezone,
            current_state=payload.current_state,
            preferred_delivery_window=payload.preferred_delivery_window,
            notification_frequency=payload.notification_frequency,
            notifications_enabled=payload.notifications_enabled,
        )
    )
    ritual = choose_ritual(profile, current_user.user_id)
    return ProfileWithRitualEnvelope(
        profile=ProfileResponse(**profile_to_dict(profile)),
        ritual=RitualResponse(**ritual),
    )


@app.get("/api/ritual/today", response_model=ProfileWithRitualEnvelope)
def ritual_today(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProfileWithRitualEnvelope:
    profile = _profile_or_404(current_user.user_id)
    return ProfileWithRitualEnvelope(
        profile=ProfileResponse(**profile_to_dict(profile)),
        ritual=RitualResponse(**choose_ritual(profile, current_user.user_id)),
    )


@app.post("/api/ritual-completions", response_model=RitualCompletionResponse)
def complete_ritual(
    payload: RitualCompletionPayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RitualCompletionResponse:
    profile = _profile_or_404(current_user.user_id)
    ritual = choose_ritual(profile, current_user.user_id)
    if payload.stable_key != ritual["stable_key"]:
        raise HTTPException(status_code=403, detail="This ritual is not assigned to the authenticated user today.")
    completed_for = datetime.now(timezone.utc).date()
    completion = completion_repository.complete(current_user.user_id, payload.stable_key, completed_for)
    return RitualCompletionResponse(
        stable_key=completion.stable_key,
        completed_for=completion.completed_for.isoformat(),
        already_completed=completion.already_completed,
        xp_awarded=completion.xp_awarded,
        diamonds_awarded=completion.diamonds_awarded,
    )


@app.get("/api/entitlement/me", response_model=EntitlementResponse)
def my_entitlement(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EntitlementResponse:
    return EntitlementResponse(**_entitlement(current_user.user_id))


frontend_dir = Path(__file__).resolve().parent.parent / "dist"
index_file = frontend_dir / "index.html"


@app.get("/dashboard", include_in_schema=False)
@app.get("/onboarding", include_in_schema=False)
@app.get("/login", include_in_schema=False)
@app.get("/signup", include_in_schema=False)
@app.get("/reading/tarot", include_in_schema=False)
@app.get("/technical-poc", include_in_schema=False)
def preview_page() -> FileResponse:
    return FileResponse(index_file)


if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
