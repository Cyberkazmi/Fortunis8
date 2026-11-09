# Fortunis8 webhook launch path

## What this adds

Fortunis8 now has an optional **Supabase Edge Function webhook** at `supabase/functions/telegram-webhook/`. It runs on Deno and does not require a continuously running Python worker or separate worker-host subscription. The Python bot remains the reference package and its full tests remain in place.

The adapter covers private-chat onboarding and language choice; fortune, tarot, palm-themed readings, horoscope-style text; Telegram Stars invoices; skill games; daily rewards; profiles and anonymous leaderboard; personas; optional kindness quests; and the last saved reading. Horoscope input is sent in one command (`/horoscope YYYY-MM-DD HH:MM, City`); birth date, time, and city are used for that response only and are not saved. Hand photos are not analyzed.

Supabase currently lists **500,000 Edge Function invocations per month on Free**. That is a quota, not unlimited production capacity; project size, usage, and inactivity limits still apply. Check the [current Supabase pricing page](https://supabase.com/pricing) before relying on a free production service.

## Security setup

Telegram cannot provide a Supabase JWT. The repo therefore sets `verify_jwt = false` **only** for `[functions.telegram-webhook]`. The handler rejects requests unless the `X-Telegram-Bot-Api-Secret-Token` header matches the configured secret. Other Edge Functions keep Supabase's default JWT verification. This follows Supabase's guidance for externally authenticated webhooks and Telegram's [webhook secret-token header](https://core.telegram.org/bots/api#setwebhook).

Set these values as **Edge Function Secrets** in the Supabase Dashboard, or through the Supabase CLI in a trusted release environment:

- `TELEGRAM_BOT_TOKEN` — the active token for this bot.
- `TELEGRAM_WEBHOOK_SECRET` — a random 32–256-character value using only `A–Z`, `a–z`, `0–9`, `_`, or `-`. Use a separate high-entropy secret; later use the same value when registering the Telegram webhook.
- `PREMIUM_PALM_PRICE_STARS` — optional; defaults to `25`, accepts `1–1000`.

Supabase injects the project URL and server-only API key into hosted functions. The code reads the current default secret-key environment or the legacy service-role variable; **never put a Supabase service key in Git, a browser, or Telegram**. Supabase reserves the `SUPABASE_` prefix for injected variables. For local development, copy `supabase/functions/.env.example` to the ignored `supabase/functions/.env` and use local-only values. Never commit the populated file. See [Supabase Edge Function secrets](https://supabase.com/docs/guides/functions/secrets).

The webhook validates the shared header in constant time, accepts only POST, caps request bodies at 256 KB, validates supported Telegram update shapes, uses a server-only key with a bounded database timeout, and returns redacted failures. It does not log incoming message content or credentials. The function has **not** been deployed, and `setWebhook` has **not** been called.

## What must happen before launch

1. Review and merge [PR #4](https://github.com/Cyberkazmi/Fortunis8/pull/4) into `main`. It is currently open and unmerged.
2. Review the new migration [`20261109081835_fortunis8_premium_redemption_idempotency.sql`](../supabase/migrations/20261109081835_fortunis8_premium_redemption_idempotency.sql). It creates only Fortunis8-owned objects. It has been parsed and statically tested locally, but **has not been applied** to Supabase. Apply it after review and verify it is recorded before deploying the updated Python or Edge code; those versions call the new RPC.
3. Deploy only `telegram-webhook` to project `lnuizsnutjdhaislsxmr` through a controlled Supabase release route. Supabase documents deployment through its CLI or CI/CD; see the [deployment guide](https://supabase.com/docs/guides/functions/deploy). This task deliberately did not deploy it.
4. Add the active bot token and separate webhook secret to Supabase Edge Function Secrets. Neither value is available in this run.
5. Only after deployment and secrets are in place, register Telegram's webhook URL with `setWebhook`, the same `secret_token`, and only the needed update types (`message`, `callback_query`, `pre_checkout_query`). Keep the Python long-polling bot stopped while webhook mode is active; Telegram does not allow polling and a webhook at the same time.
6. Run private-chat checks for language, readings, horoscope privacy, games, rewards, and callbacks. Test a Stars purchase only after intentionally reviewing and approving the live invoice.

## Retry behavior and limits

The new migration adds an atomic RPC keyed by Telegram `update_id` and a receipt/result table for premium-reading redemption. A repeat of the same update returns the stored outcome and cannot deduct a second credit. It records no-credit outcomes too, so replaying an old callback cannot later consume a newly purchased credit. The Python and Deno handlers pass the update ID and show a neutral “already processed” response instead of generating or sending a different reading.

This is **premium-redemption idempotency**, not a general receipt for every Telegram update. Other repeated deliveries may repeat a free reading/history row, a reply, or an invoice; creating another invoice does not charge the user unless they explicitly complete Telegram's purchase flow. The Star charge ledger, daily rewards, games, and charity claims retain their existing narrower idempotency checks.

## Database status

The existing project records `20261109071117 / fortunis8_step1_users` and `20261109073612 / fortunis8_core`; both are represented in `supabase/migrations/` under their exact recorded names. Do not rerun them. The new `20261109081835_fortunis8_premium_redemption_idempotency` migration is pending review and is **not applied**. No existing product table is altered by it.
