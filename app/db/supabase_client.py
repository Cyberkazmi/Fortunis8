from __future__ import annotations

from typing import Any

from supabase import create_client

from app.config import settings

_SUPABASE_CLIENT: Any | None = None


def build_supabase_client() -> Any:
    settings.validate_supabase()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_client() -> Any:
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        _SUPABASE_CLIENT = build_supabase_client()
    return _SUPABASE_CLIENT


def reset_supabase_client() -> None:
    global _SUPABASE_CLIENT
    _SUPABASE_CLIENT = None
