# Fortunis8 validation

## Local checks

The package was checked with the repository's declared dependencies in an isolated Python 3.12 environment.

- Full `pytest` suite: **50 passed**. The one remaining warning is a third-party Starlette deprecation notice about `python_multipart`.
- `python -m compileall -q app tests`: passed.
- Real `python-telegram-bot` Application construction with a synthetic test-only token: passed; 37 handlers registered across groups `-2`, `-1`, and `0`. No Telegram API request was made, and no Supabase store was configured for this construction test.
- `pglast` SQL parsing: `supabase/migrations/20261109071117_fortunis8_step1_users.sql` parsed as 10 statements; `supabase/migrations/20261109073612_fortunis8_core.sql` parsed as 40 statements. This parses the SQL migration envelope but does not execute the PL/pgSQL functions.
- Static migration checks confirm the core migration creates only `fortunis8_*` tables, enables RLS on those new tables, and does not drop or alter the existing product tables.
- Read-only Supabase verification confirmed history rows `20261109071117 / fortunis8_step1_users` and `20261109073612 / fortunis8_core`; the seven Fortunis8 tables' columns/types/nullability, checks, keys, foreign keys and indexes match the migration DDL, all seven have RLS enabled, and the expected RPC signatures plus `fortunis8_set_updated_at` trigger exist. No database writes were made.
- `git diff --check`: passed.

## Not live-tested

The local test suite used mocks; it made no live Supabase requests. A separate read-only schema/history inspection confirmed the deployed migration records and Fortunis8 object structure. The bot was not connected to Telegram, no live write or Telegram Stars transaction was attempted, and production connectivity is untested. The Supabase CLI binary was unavailable in this environment, so `supabase migration list`/`db push` were not run; the files now follow the CLI's standard path and exact remote version/name records.

The changes are on `feat/fortunis8-bilingual-bot`; [PR #4 is open against `main` and not merged](https://github.com/Cyberkazmi/Fortunis8/pull/4). See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the remaining account-side steps.
