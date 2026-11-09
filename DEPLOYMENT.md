# Fortunis8 deployment

## What this package runs

Fortunis8 is a private-chat Telegram bot using Supabase for saved language, points, readings, game sessions, and Telegram Stars entitlements. Its new reading templates are deterministic and do not require an OpenAI key. Palm readings are text reflections based on a chosen topic; uploaded hand photos are not analyzed. Horoscope input uses a tropical sun-sign label and a playful time/location theme, not a full astronomical kundli. All readings are entertainment only.

The default detailed palm-reading price is **25 Telegram Stars**, configurable with `PREMIUM_PALM_PRICE_STARS` (1–1000). Diamonds are earned through free daily claims, skill games, and optional positive quests; they are not purchasable or redeemable for cash. BNB/crypto rewards are not enabled.

## Important current status

PR [#4 is open against `main`](https://github.com/Cyberkazmi/Fortunis8/pull/4) and remains unmerged. The Telegram bot has not been connected or live-tested. Supabase records the applied migrations as `20261109071117 / fortunis8_step1_users` and `20261109073612 / fortunis8_core`; the repository files now use those exact version/name pairs. **Do not manually rerun either migration.** Existing project tables were not changed.

Canonical source: [Cyberkazmi/Fortunis8](https://github.com/Cyberkazmi/Fortunis8) (`main`; local starting commit `518a92f`). Existing database project ID `lnuizsnutjdhaislsxmr` uses `https://lnuizsnutjdhaislsxmr.supabase.co`. Its existing `profiles`, `fortune_readings`, `rewards`, `quests`, `daily_streaks`, and `mini_games` tables were inspected read-only and are untouched by these changes.

## Supabase CLI migration tracking

The applied files are in the CLI's standard `supabase/migrations/` directory: `20261109071117_fortunis8_step1_users.sql` and `20261109073612_fortunis8_core.sql`. Their timestamp prefixes and names match the remote rows in `supabase_migrations.schema_migrations`, so the CLI can recognize them as already applied. Before any future `supabase db push`, link the intended project and check `supabase migration list`; do not use migration repair for these versions. See the [Supabase local migration guide](https://supabase.com/docs/guides/local-development/database-migrations) and [deployment migration guide](https://supabase.com/docs/guides/deployment/database-migrations) for how the CLI discovers migrations and compares them to remote history.

## Setup steps

1. **Database setup is complete for this project.** `20261109071117_fortunis8_step1_users.sql` and `20261109073612_fortunis8_core.sql` are already applied and verified. For a separate fresh project, apply them in order; never run the original `fortunis8_mvp_schema.sql` over the existing database.
2. **Prepare the Telegram bot** with BotFather. Use a newly issued, active token. Never use a token previously exposed in source/chat.
3. **After PR review and merge, connect the updated source** to a Python worker host that supports a continuously running process. This bot uses Telegram long polling, so run one replica and do not configure a webhook. No public inbound port is required.
4. **Set these values in the host's secret/environment settings** (not in source files or chat):
   - `TELEGRAM_BOT_TOKEN` — Secret: the active token for the Fortunis8 bot.
   - `SUPABASE_URL` — `https://lnuizsnutjdhaislsxmr.supabase.co` (the existing Fortunis8 project).
   - `SUPABASE_SECRET_KEY` — Secret: Supabase server-only secret key beginning `sb_secret_`. Never use a publishable/anon key here.
   - `APP_ENV=production`
   - `PREMIUM_PALM_PRICE_STARS=25` (or your chosen 1–1000 Stars price).
   - `OPENAI_API_KEY` is optional for the new deterministic MVP flows; older AI modules may use it if invoked.
5. **Use the start command** `python -m app.main` with Python 3.10 or newer. Keep the host's logs private; the new Fortunis8 handlers avoid logging credentials and user message bodies.
6. **Run a controlled private-chat check**: `/start`, switch English/Urdu, open `/menu`, try `/fortune`, `/tarot`, `/horoscope`, `/palm`, `/games`, `/daily`, `/profile`, `/leaderboard`, `/personas`, `/charity`, and `/last`. Use Telegram's Stars flow only after reviewing and intentionally approving any live charge.

## Privacy and safeguards

- Supabase service-role secret and Telegram token remain server-side; Supabase REST errors are redacted.
- Horoscope birth date, time, and location are used for a single response but are not stored in Supabase.
- Users can view anonymous numeric leaderboard scores; Telegram IDs and names are not shown there.
- Game answers are bound to short-lived database sessions and checked server-side; retries cannot award twice.
- Daily and charity rewards are idempotent; charity actions are voluntary and require no donation or proof.
- Telegram Stars payments are verified against a saved user-bound invoice, XTR currency, exact price, expiry, and Telegram charge ID before the entitlement is recorded.
- `/last` can retrieve the last saved reading if Telegram delivery is interrupted after the reading was stored.

## Remaining before live operation

A live start still requires the feature branch to be reviewed and merged, the resulting source to be placed on a chosen host, and the host's secret settings to receive the active Telegram token and Supabase server key. Database migrations are already applied. Automated tests do not prove live Telegram delivery, an actual Stars payment, or production bot connectivity.
