# Fortunis8 deployment

## What this package runs

Fortunis8 is an English/Urdu Telegram entertainment bot. It includes fortune/tarot/palm-themed text, a horoscope-style reading, Telegram Stars for a detailed reading, skill games, daily diamonds, an anonymous leaderboard, personas, and optional positive quests. No reading guarantees an outcome or gives professional advice; hand photos are not analyzed and birth details are not retained.

The default detailed-reading price is **25 Telegram Stars**, configurable from 1–1000. Diamonds are earned, not purchased or cash-redeemable. BNB/crypto rewards are not enabled.

## Recommended route: Supabase Edge Function

The repository includes a Deno/TypeScript Telegram webhook at `supabase/functions/telegram-webhook/`. It avoids a separate always-on worker host. Supabase currently lists 500,000 Edge Function invocations monthly on Free, subject to the plan's other usage and inactivity limits; check [current pricing](https://supabase.com/pricing).

See the step-by-step [Edge Function launch guide](docs/edge-function-launch.md) for exact secrets, the webhook header check, rollout order, and retry boundaries. The function has **not** been deployed and Telegram's `setWebhook` has **not** been called.

## Alternative: Python long-polling worker

The tested Python application remains available for one continuously active process. Use `python -m app.main` with Python 3.10 or newer and server-side values for `TELEGRAM_BOT_TOKEN`, `SUPABASE_URL`, and `SUPABASE_SECRET_KEY` (or the supported server-only equivalent). Do not run multiple polling replicas. Stop polling before enabling Telegram webhook mode; Telegram cannot use both modes at once.

## Current release and database status

PR [#4 is open against `main`](https://github.com/Cyberkazmi/Fortunis8/pull/4) and remains unmerged. The canonical project is [Cyberkazmi/Fortunis8](https://github.com/Cyberkazmi/Fortunis8). The existing Supabase project is `lnuizsnutjdhaislsxmr` (`https://lnuizsnutjdhaislsxmr.supabase.co`).

The database already records `20261109071117 / fortunis8_step1_users` and `20261109073612 / fortunis8_core`, represented in `supabase/migrations/` with those exact names. Do not rerun either. The new additive migration [`20261109081835_fortunis8_premium_redemption_idempotency.sql`](supabase/migrations/20261109081835_fortunis8_premium_redemption_idempotency.sql) is **not applied**. Review and apply it before deploying updated Python or Edge code, since both now call its `fortunis8_redeem_premium_reading_for_update` RPC. It creates only a Fortunis8-owned receipt table and server-only RPC; it does not modify existing product tables.

## Before live operation

An active Telegram bot token is not available to this run. After the PR and migration have been reviewed and the migration applied, deploy the webhook, install the bot token and separate webhook secret in Supabase Function Secrets, then register `setWebhook`. Do not set the webhook before the endpoint is deployed and configured. No deployment, webhook registration, or live Stars transaction was performed here.
