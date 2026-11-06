# Fortunis8 Phase 2B isolated MVP review package

This directory is the single review index for the Phase 2B MVP. The implementation remains separated by runtime responsibility, but every deliverable is linked from this location so the architect, product owner, and database owner can review one package without searching the repository.

## Review status

The isolated MVP is implemented on `manus-sync` and proposed for merge through [PR #3](https://github.com/Cyberkazmi/Fortunis8/pull/3). It has been validated with 49 passing Python tests, a successful Vite build, and a successful multi-stage Docker image build. The container served `/health`, `/`, `/onboarding`, `/dashboard`, and `/reading/tarot` successfully; unauthenticated protected API access returned HTTP 401.

This is not final production work. No live Supabase project was connected, no Supabase migration was executed, and no production credential was used. The isolated preview uses in-memory profile, entitlement, and completion repositories. Its sandbox-only preview token is disabled by default.

## Deliverable map

| Area | Authoritative location | Purpose |
|---|---|---|
| Product blueprint | [`product-blueprint.md`](../../product-blueprint.md) | Customer journey, page hierarchy, belief-flexible product direction, and delivery pipeline. |
| Schema design | [`schema-design.md`](../../schema-design.md) | Identity, profile, goals, preferences, rituals, progression, notifications, and ownership model. |
| Ritual blueprint | [`template-ritual-blueprint.md`](../../template-ritual-blueprint.md) | Template-based onboarding and daily ritual assignment rules. |
| Catalog content | [`seeds/fortunis8_catalog.json`](../../seeds/fortunis8_catalog.json) and [`seeds/fortunis8_catalog_seed.sql`](../../seeds/fortunis8_catalog_seed.sql) | Draft bilingual goals, guidance modes, states, traditions, and rituals. |
| Database artifacts | [`supabase/migrations/`](../../supabase/migrations/) | Additive ritual, subscription, and Phase 2B auth/RLS migrations. These are unapplied source artifacts. |
| Web runtime | [`web-poc/`](../../web-poc/) | React/Vite frontend, FastAPI backend, Dockerfile, route manifest, and runtime notes. |
| Auth and ownership | [`web-poc/backend/auth.py`](../../web-poc/backend/auth.py), [`web-poc/backend/profile_repository.py`](../../web-poc/backend/profile_repository.py) | Verified bearer tokens, token-derived ownership, in-memory isolation, and server-only Supabase adapter. |
| Ritual and AI service | [`web-poc/backend/ai_ritual_service.py`](../../web-poc/backend/ai_ritual_service.py) | Strict JSON-schema AI generation with Pydantic validation and catalog fallback. |
| Completion rewards | [`web-poc/backend/completion_service.py`](../../web-poc/backend/completion_service.py) | Idempotent server-authoritative XP and diamond awards. |
| Telegram preservation | [`app/bot/`](../../app/bot/) and [`app/bot/local_test_bot.py`](../../app/bot/local_test_bot.py) | Existing bot behavior plus a polling-only in-memory local test flow. |
| Tests | [`tests/`](../../tests/) | Existing bot tests plus authenticated web, entitlement, AI contract, ownership, and completion coverage. |
| Architecture handoff | [`FORTUNIS8_ARCHITECT_HANDOFF.md`](../../FORTUNIS8_ARCHITECT_HANDOFF.md) | Evidence-led implementation and production-gate report. |
| Self-account | [`docs/FORTUNIS8_COMPLETE_SELF_ACCOUNT.md`](../FORTUNIS8_COMPLETE_SELF_ACCOUNT.md) | Chronology, decisions, challenges, and blueprint adherence. |

## Isolated MVP run modes

For a no-credential local test, use the default in-memory mode:

```bash
/tmp/fortunis8-deps-venv/bin/python -m pytest -q
cd web-poc
npx --no-install vite build
WEB_POC_PROFILE_REPOSITORY=memory FORTUNIS8_AI_MODE=off \
  /tmp/fortunis8poc-venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 3000
```

For the interactive sandbox preview only, the server may be started with `WEB_POC_PREVIEW_AUTH=true`, `WEB_POC_PROFILE_REPOSITORY=memory`, and `FORTUNIS8_AI_MODE=live`. The preview token is `preview-token` only in that explicitly enabled sandbox mode; it must not be used in production.

## Supabase gate

Supabase end-to-end verification is intentionally still open. To complete it safely, the owner must provide a separate non-production Supabase project and configure `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, and the server-only `SUPABASE_SERVICE_ROLE_KEY` through the approved secret channel. The database owner must review and apply the three migration artifacts in order in that isolated project, then run authenticated profile, ritual assignment, entitlement, and completion checks there.

Until that gate is completed, the MVP must be described as isolated and in-memory rather than persistent or Supabase-connected. No final production work should begin before explicit owner approval of the isolated Supabase results.
