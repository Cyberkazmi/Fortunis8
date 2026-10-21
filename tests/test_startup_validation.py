import os

import pytest

from app.config import Settings


def test_validate_requires_telegram_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        Settings.validate()


def test_validate_allows_missing_ai_on_startup(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert Settings.validate() is True


def test_validate_ai_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        Settings.validate_ai()


def test_validate_supabase_requires_url_and_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SUPABASE_KEY"):
        Settings.validate_supabase()


def test_validate_supabase_rejects_invalid_url(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "not-a-url")
    monkeypatch.setenv("SUPABASE_KEY", "key")
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        Settings.validate_supabase()
