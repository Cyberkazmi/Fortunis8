from __future__ import annotations

from typing import Any

from supabase import create_client

from app.config import settings


def build_supabase_client():
    settings.validate_supabase()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_client() -> Any:
    return build_supabase_client()
