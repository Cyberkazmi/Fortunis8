import pytest

from app.config import Settings


def set_base(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_fixture")
    monkeypatch.setenv("PREMIUM_PALM_PRICE_STARS", "25")
    monkeypatch.setenv("APP_ENV", "staging")


def test_fortunis8_settings_accept_server_secret(monkeypatch):
    set_base(monkeypatch)
    assert Settings.validate_fortunis8() is True


def test_fortunis8_settings_reject_publishable_key(monkeypatch):
    set_base(monkeypatch)
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_publishable_not-server-secret")
    with pytest.raises(RuntimeError, match="sb_secret_"):
        Settings.validate_fortunis8()


def test_fortunis8_settings_reject_non_https_remote_url(monkeypatch):
    set_base(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "http://example.supabase.co")
    with pytest.raises(RuntimeError, match="HTTPS"):
        Settings.validate_fortunis8()


def test_fortunis8_settings_reject_out_of_range_stars_price(monkeypatch):
    set_base(monkeypatch)
    monkeypatch.setenv("PREMIUM_PALM_PRICE_STARS", "0")
    with pytest.raises(RuntimeError, match="between 1 and 1000"):
        Settings.validate_fortunis8()
