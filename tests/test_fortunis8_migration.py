from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "supabase" / "migrations"
USERS_MIGRATION = MIGRATION_DIR / "20261109071117_fortunis8_step1_users.sql"
MIGRATION = MIGRATION_DIR / "20261109073612_fortunis8_core.sql"
IDEMPOTENCY_MIGRATION = MIGRATION_DIR / "20261109081835_fortunis8_premium_redemption_idempotency.sql"


def test_cli_migration_filenames_match_recorded_supabase_history():
    recorded = (
        ("20261109071117", "fortunis8_step1_users"),
        ("20261109073612", "fortunis8_core"),
    )
    assert (ROOT / "supabase" / "config.toml").is_file()
    assert all((MIGRATION_DIR / f"{version}_{name}.sql").is_file() for version, name in recorded)
    assert IDEMPOTENCY_MIGRATION.is_file()
    assert IDEMPOTENCY_MIGRATION.name not in {f"{version}_{name}.sql" for version, name in recorded}
    assert not (ROOT / "migrations").exists()


def test_users_migration_matches_step_one_table():
    sql = USERS_MIGRATION.read_text().lower()
    assert "create table if not exists public.fortunis8_users" in sql
    assert "alter table public.fortunis8_users enable row level security" in sql
    assert "revoke all on table public.fortunis8_users from anon, authenticated" in sql
    assert "grant select, insert, update on table public.fortunis8_users to service_role" in sql


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


def test_pending_premium_redemption_migration_is_additive_and_update_keyed():
    sql = IDEMPOTENCY_MIGRATION.read_text().lower()
    assert "create table if not exists public.fortunis8_premium_redemption_receipts" in sql
    assert "telegram_update_id bigint primary key" in sql
    assert "alter table public.fortunis8_premium_redemption_receipts enable row level security" in sql
    assert "revoke all on table public.fortunis8_premium_redemption_receipts from anon, authenticated" in sql
    assert "grant all on table public.fortunis8_premium_redemption_receipts to service_role" in sql
    assert "function public.fortunis8_redeem_premium_reading_for_update" in sql
    assert "on conflict (telegram_update_id) do nothing" in sql
    assert "on delete cascade" not in sql
    assert "'duplicate', true" in sql
    assert "drop table" not in sql
    assert not re.search(
        r"alter\s+table\s+public\.(profiles|fortune_readings|rewards|quests|daily_streaks|mini_games)\b",
        sql,
    )
