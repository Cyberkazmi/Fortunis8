# Fortunis8

Fortunis8 is a science-informed, belief-flexible daily growth platform with template-based rituals, reflection, quests, rewards, and an optional Telegram experience.

## Project goals

- Deliver personalized daily rituals shaped by user-selected goals and guidance modes.
- Reward users through diamonds, streaks, XP, levels, and quests.
- Offer optional tarot, horoscope, fortune, and palm interpretation as reflection prompts, never guaranteed predictions.
- Build a modular Python app that can scale into a bot + API + web dashboard.

## Architecture overview

This project follows a clean layered architecture:

- `app/bot` handles Telegram commands, conversations, and the local test bot.
- `app/services` contains business logic and integrations.
- `app/models` defines domain objects.
- `app/db` communicates with Supabase when explicitly enabled.
- `app/api` exposes future API endpoints.
- `web-poc` contains the isolated React/FastAPI product preview.
- `tests` contains validation tests.

## Recommended build order

1. Core app bootstrap and configuration
2. Database connectivity and Supabase client
3. User and ritual profile models
4. Personalized ritual assignment and notifications
5. Telegram and web onboarding
6. Rewards, quests, and progression
7. Reading history and optional reflection experiences
8. Testing and deployment

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

## Run the test bot locally

Use a dedicated Telegram test-bot token supplied through the environment only. The harness uses polling, starts at `/start`, and offers button-only goal, belief-mode, and rhythm choices before returning a first ritual. Profiles are held in an in-memory repository; it does not connect to Supabase, write real users, schedule notifications, or configure a webhook.

```bash
export TELEGRAM_BOT_TOKEN='your-test-bot-token'
python -m app.bot.local_test_bot
```

Never commit the token or place it in source code, logs, tests, or `.env.example`.

## Environment variables

Create a `.env` file using `.env.example`. The production bot requires `TELEGRAM_BOT_TOKEN`; AI and Supabase credentials are only loaded by the features that explicitly need them.

## Notes

The migrations in `supabase/migrations/` are committed source artifacts only. They must be reviewed and run by the database owner; this local POC does not execute them.
