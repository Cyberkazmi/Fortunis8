# Fortunis8

Fortunis8 is a mystical AI-powered fortune application designed around Telegram interactions, reward loops, and personalized reading experiences.

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
- `app/api` exposes future API endpoints.
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

This is a starter architecture meant to be expanded into a more complete production-ready app.
