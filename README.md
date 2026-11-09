# Fortunis8

## Current implementation

The repository now includes a bilingual English/Urdu Telegram MVP alongside its original service modules: entertainment-only fortune and tarot readings, basic and premium text-based palm reflections, a sun-sign horoscope-style flow, Telegram Stars premium-reading entitlement, server-verified skill games, daily rewards, anonymous leaderboard, selectable personas, and optional positive quests. See [`DEPLOYMENT.md`](DEPLOYMENT.md) and [`VALIDATION.md`](VALIDATION.md) for the current setup and test boundary.

The current code does not analyze hand photos, calculate a full astronomical kundli, sell diamonds, issue BNB payouts, or claim that readings predict outcomes. Birth date, time, and location are used transiently and are not saved. Do not run the original `fortunis8_mvp_schema.sql` against the existing project.

Fortunis8 is a Telegram entertainment bot with bilingual readings, skill-based progression, and privacy-conscious persistence.

## Project goals

- Deliver spiritual, story-rich fortune readings.
- Reward users through diamonds, streaks, and quests.
- Offer tarot, horoscope, and palm-reading experiences.
- Build a modular Python app that can scale into a bot + API + future web dashboard.

## Architecture overview

This project follows a clean layered architecture:

- `app/bot` handles Telegram commands and conversations.
- `app/services` contains business logic and integrations.
- `app/models` defines domain objects.
- `app/db` communicates with Supabase.
- `app/api` contains separate health/readiness routes; the current worker command runs Telegram polling only.
- `app/utils` stores shared helpers and AI prompt templates.
- `tests` contains validation tests.

## Recommended build order

1. Core app bootstrap and configuration
2. Database connectivity and Supabase client
3. User and fortune models
4. AI fortune generation service
5. Telegram bot entry points
6. Rewards and quests logic
7. Reading history and onboarding flow
8. Testing and deployment setup

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

## Environment variables

Create a `.env` file using `.env.example`.

## Notes

The original service modules remain in place for compatibility. The new private-chat feature flows are registered first; see the current deployment and validation guides before enabling a host.
