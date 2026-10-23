import os

import pytest

from app.config import Settings


def test_imports_are_safe_without_live_credentials(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    Settings.reload()
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        Settings.validate()


def test_validate_requires_telegram_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    Settings.reload()
    assert Settings.validate() is True


def test_validate_ai_requires_key(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    Settings.reload()
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        Settings.validate_ai()


def test_validate_supabase_requires_url_and_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    Settings.reload()
    with pytest.raises(RuntimeError, match="SUPABASE_KEY"):
        Settings.validate_supabase()
