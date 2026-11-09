# Fortunis8 validation

## Local checks

The package was checked with the repository's declared dependencies in an isolated Python 3.12 environment.

- Full `pytest` suite: **50 passed**. The one remaining warning is a third-party Starlette deprecation notice about `python_multipart`.
- `python -m compileall -q app tests`: passed.
- Real `python-telegram-bot` Application construction with a synthetic test-only token: passed; 37 handlers registered across groups `-2`, `-1`, and `0`. No Telegram API request was made, and no Supabase store was configured for this construction test.
- `pglast` SQL parsing: migration `20261109_001_fortunis8_users.sql` parsed as 10 statements; `20261109_002_fortunis8_core.sql` parsed as 40 statements. This parses the SQL migration envelope but does not execute the PL/pgSQL functions.
- Static migration checks confirm the core migration creates only `fortunis8_*` tables, enables RLS on those new tables, and does not drop or alter the existing product tables.
- `git diff --check`: passed.

## Not live-tested

Migrations `20261109_001_fortunis8_users.sql` and `20261109_002_fortunis8_core.sql` have since been applied and verified on the existing Supabase project. The bot was not connected to Telegram, this local test run made no live Supabase request, and no Telegram Stars transaction was attempted. A passing local suite therefore does not certify production credentials, provider availability, live payment handling, or a deployed bot.

The changes are being carried on a dedicated feature branch and are not merged to `main`. See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the remaining account-side steps.
