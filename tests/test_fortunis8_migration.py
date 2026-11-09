from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "20261109_002_fortunis8_core.sql"


def test_core_migration_creates_only_fortunis8_tables():
    sql = MIGRATION.read_text().lower()
    created = re.findall(r"create table if not exists\s+([a-z0-9_.]+)", sql)
    assert created
    assert all(name.startswith("public.fortunis8_") for name in created)
    assert "public.profiles" not in " ".join(created)
    assert "public.fortune_readings" not in " ".join(created)


def test_core_migration_enables_rls_and_keeps_client_roles_out():
    sql = MIGRATION.read_text().lower()
    for table in (
        "fortunis8_accounts", "fortunis8_events", "fortunis8_readings",
        "fortunis8_game_sessions", "fortunis8_pending_invoices", "fortunis8_star_payments",
    ):
        assert f"alter table public.{table} enable row level security" in sql
    assert "from anon, authenticated" in sql
    assert "to service_role" in sql


def test_core_migration_has_no_drop_or_alter_of_legacy_tables():
    sql = MIGRATION.read_text().lower()
    assert "drop table" not in sql
    assert not re.search(r"alter\s+table\s+public\.(profiles|fortune_readings|rewards|quests|daily_streaks|mini_games)\b", sql)


def test_core_migration_contains_idempotent_daily_game_and_stars_operations():
    sql = MIGRATION.read_text().lower()
    for function in (
        "fortunis8_claim_daily", "fortunis8_complete_game",
        "fortunis8_claim_charity_quest", "fortunis8_record_star_payment",
        "fortunis8_redeem_premium_reading",
    ):
        assert f"function public.{function}" in sql
    assert "idempotency_key text not null unique" in sql
    assert "telegram_payment_charge_id text not null unique" in sql
    assert "p_currency <> 'xtr'" in sql
