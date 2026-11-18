# Fortunis8 validation

## Checks run

- Full Python suite: **55 passed** in the isolated Python 3.12 environment; one third-party Starlette deprecation warning remains. Tests cover update-ID pass-through in Python redemption and same-ID replay handling.
- Deno 2 formatting, lint, and TypeScript checks passed. **12 webhook tests passed**, covering authentication, private-chat flow, malformed updates, Stars checks, horoscope privacy, and premium redemption replay with the same update ID.
- `pglast` parsed all **9 top-level statements** in the premium-redemption migration; `supabase/config.toml` parsed as valid TOML. Static tests verify Fortunis8-only objects, RLS, client-role restrictions, the server-role grant, update-ID receipt key, and duplicate-result behavior.
- A disposable local PGlite PostgreSQL-compatible engine executed the three Fortunis8 migration SQL files. It confirmed that a same-ID replay does not deduct a second credit or create a second reading/event; mismatched focus is rejected; a no-credit outcome stays no-credit when replayed after the balance changes; and a new update ID can redeem once.
- The live project migration record supplied for this release is `20261109082951 / fortunis8_premium_redemption_idempotency`; the receipt table is present with RLS enabled and the RPC exists. The repository file is now named `20261109082951_fortunis8_premium_redemption_idempotency.sql`. Its SQL body is byte-for-byte unchanged from the prior versioned filename; only the path/name changed. Existing migration history is `20261109071117 / fortunis8_step1_users` and `20261109073612 / fortunis8_core`.

## Not live-tested

No Edge Function deployment, Telegram webhook registration, live bot message, or Stars transaction was performed in this task. The live migration verification comes from the supplied applied-version/schema confirmation; a fresh read-only Supabase CLI/MCP query could not authenticate in this run. The local PGlite execution is not a hosted Supabase rollout. PR [#4](https://github.com/Cyberkazmi/Fortunis8/pull/4) remains open against `main` and unmerged. See [`DEPLOYMENT.md`](DEPLOYMENT.md) and [`docs/edge-function-launch.md`](docs/edge-function-launch.md).
