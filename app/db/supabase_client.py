from supabase import create_client

from app.config import settings


def build_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise RuntimeError(
            "Supabase credentials are missing. Set SUPABASE_URL and SUPABASE_KEY before starting Fortunis8."
        )

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


supabase = build_supabase_client()
