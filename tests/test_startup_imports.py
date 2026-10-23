from __future__ import annotations

import importlib

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def reset_supabase_client_after_test():
    yield
    from app.db import supabase_client

    supabase_client.reset_supabase_client()


def test_app_modules_import_without_live_credentials(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    settings.reload()

    import app.main
    import app.bot.handlers
    import app.services.user_service
    import app.services.telegram_service
    import app.services.fortune_service
    import app.db.supabase_client

    assert app.main is not None
    assert app.bot.handlers is not None
    assert app.services.user_service is not None
    assert app.services.telegram_service is not None
    assert app.services.fortune_service is not None
    assert app.db.supabase_client is not None


def test_build_application_resolves_from_user_service():
    from app.bot.handlers import build_application
    from app.services.user_service import build_application as user_build_application

    assert build_application is user_build_application


def test_startup_validation_runs_before_application_construction(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    settings.reload()

    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        from app.services.user_service import build_application
        build_application()


def test_supabase_client_is_lazy_reused_and_reset(monkeypatch):
    import app.db.supabase_client as supabase_client_module

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "mock-key")
    settings.reload()

    sentinel = object()
    calls = []

    def fake_create_client(url, key):
        calls.append((url, key))
        return sentinel

    monkeypatch.setattr(supabase_client_module, "create_client", fake_create_client)
    supabase_client_module.reset_supabase_client()

    client1 = supabase_client_module.get_supabase_client()
    client2 = supabase_client_module.get_supabase_client()

    assert client1 is sentinel
    assert client1 is client2
    assert len(calls) == 1

    supabase_client_module.reset_supabase_client()
    client3 = supabase_client_module.get_supabase_client()
    assert client3 is sentinel
    assert len(calls) == 2


def test_supabase_client_does_not_create_on_import():
    import app.db.supabase_client as supabase_client_module

    assert supabase_client_module._SUPABASE_CLIENT is None
