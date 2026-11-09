# Fortunis8 validation

## Checks run

- Full Python suite: **55 passed** in the isolated Python 3.12 environment; one third-party Starlette deprecation warning remains. Tests cover update-ID pass-through in Python redemption and same-ID replay handling.
- Deno 2 formatting, lint, and TypeScript checks passed. **12 webhook tests passed**, covering authentication, private-chat flow, malformed updates, Stars checks, horoscope privacy, and premium redemption replay with the same update ID. Commands: `npx --yes deno@2 fmt supabase/functions/telegram-webhook/*.ts`; `npx --yes deno@2 lint supabase/functions/telegram-webhook`; `npx --yes deno@2 check supabase/functions/telegram-webhook/index.ts supabase/functions/telegram-webhook/handler_test.ts`; `npx --yes deno@2 test --allow-read=supabase/config.toml supabase/functions/telegram-webhook/handler_test.ts`.
- `pglast` parsed all **9 top-level statements** in the pending migration and `supabase/config.toml` parsed as valid TOML. Static tests check that the migration adds only Fortunis8 objects, enables RLS, denies client roles, grants access only to `service_role`, keys receipts by `telegram_update_id`, and returns stored results on duplicate input.
- A disposable local PGlite PostgreSQL-compatible engine executed the two existing Fortunis8 migrations plus the pending migration. It confirmed that the first premium redemption consumes one credit and creates one reading/event; the same update ID returns the same reading with no second deduction; a different focus for the same ID is rejected; a no-credit result remains no-credit when replayed after the balance changes; and a new update ID can redeem once. This test used local synthetic data only, not Supabase.
- The previously applied remote migration history/schema for `20261109071117 / fortunis8_step1_users` and `20261109073612 / fortunis8_core` was read-only verified in the earlier validation pass. The new migration is **pending review and unapplied**; no remote database was written.

## Not live-tested

No live Telegram or Supabase request, webhook registration, Edge Function deployment, or Stars transaction was performed. The updated Python and Deno code call the new RPC, so do not deploy them until the migration is reviewed and applied. The local PGlite execution is not a hosted Supabase rollout. See [`DEPLOYMENT.md`](DEPLOYMENT.md) and [`docs/edge-function-launch.md`](docs/edge-function-launch.md).

PR [#4](https://github.com/Cyberkazmi/Fortunis8/pull/4) remains open against `main` and unmerged.
