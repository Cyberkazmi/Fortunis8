# Fortunis8 System Architect Handoff

**Date:** 2026-11-02  
**Repository:** `Cyberkazmi/Fortunis8`  
**Active branch:** `manus-sync`  
**Current commit:** `22fba68c4e92775846a2469af722a5d55a349404`  
**Branch state:** Clean and aligned with `origin/manus-sync`

## 1. Executive summary

Fortunis8 has evolved from a Telegram proof of concept into an isolated, science-informed, belief-flexible daily growth platform prototype. The current product direction is:

> Users select goals, guidance preferences, rhythm, language, and optional reading preferences through templates. Fortunis8 assigns small daily rituals, turns completion into quests and progression, and optionally provides symbolic readings as reflection prompts rather than guaranteed predictions.

The current implementation successfully demonstrates the product experience and the first connected web flow:

1. A consumer-facing landing page explains the product.
2. Template-based onboarding captures a user-selected profile.
3. The profile is submitted to a FastAPI endpoint.
4. A deterministic catalog ritual is assigned using the selected goals, belief mode, and duration.
5. The dashboard retrieves and displays the assigned ritual.
6. Free/Premium limits are enforced by a schema-shaped in-memory entitlement repository.
7. The existing Telegram application, quest/reward logic, streak logic, and tests remain preserved.

This is **not yet a production SaaS**. Authentication, durable persistence, Supabase/RLS execution, real notification scheduling, payment processing, production entitlement lookup, and server-side completion/reward accounting remain to be implemented.

## 2. Current project phase

### Current phase: Phase 2A — integrated product POC / architecture validation

The project is beyond the isolated visual/Webdev POC and is now at the first integrated product-flow checkpoint. The current phase proves the product loop without connecting production services:

- Product-oriented web UI exists.
- React frontend communicates with FastAPI.
- Profile creation and ritual assignment are connected.
- Catalog-driven matching is implemented.
- Entitlement limits are enforced.
- Telegram behavior remains intact.
- Tests and frontend build pass.

The work should not yet be described as a production release or a complete MVP. The next major phase is **Phase 2B — authenticated, persistent MVP integration**.

## 3. Historical progression

### Phase 0 — production-readiness baseline

The original repository contained the Telegram application, FastAPI/service structure, configuration validation, reward/streak work, and production-readiness fixes. Earlier work included:

- Resolving the `python-telegram-bot` / `httpx` dependency conflict.
- Fixing startup validation so a missing `TELEGRAM_BOT_TOKEN` raises the intended `RuntimeError` rather than `telegram.error.InvalidToken`.
- Fixing test isolation around the Supabase client state.
- Preserving the existing Telegram command and quest behavior.
- Reaching the production-readiness candidate state before product expansion.

### Phase 1 — product blueprint and isolated Web POC

The technical connectivity demo was redesigned into a consumer-facing product preview. The landing page and dashboard were changed from backend-test language into an actual Fortunis8 experience:

- Public landing page with value proposition and calls to action.
- Template-based onboarding preview.
- Daily ritual dashboard preview.
- Optional tarot, horoscope, fortune, and palm reflection pages.
- XP, levels, streaks, diamonds, quests, history, and premium-preview surfaces.
- Sky-blue landing/application theme and darker reading surfaces.
- Mobile-first responsive layout with bottom navigation.

The isolated POC intentionally avoided production credentials, Supabase connections, AI reading generation, and database writes.

### Phase 1B — catalog and schema design

The product model was expanded to support multiple user goals and belief-flexible guidance:

- 13 goal paths:
  - `business_wealth`
  - `study_exams`
  - `career_interview`
  - `health_energy`
  - `stress_calm`
  - `relationships`
  - `creativity`
  - `discipline`
  - `spiritual_reflection`
  - `religious_routine`
  - `confidence`
  - `life_transition`
  - `sleep_recovery`
- Bilingual catalog seed content in English and Urdu.
- 28 draft rituals with goal and guidance-mode tags.
- Catalog JSON and SQL seed artifacts.
- Draft ritual-platform and subscription migrations.

The migration files are committed source artifacts only. They were not executed by Manus and no live Supabase project was touched.

### Phase 1C — Telegram path and progression prototype

A Telegram prototype was added for template-based onboarding and quest progression. The application retains the existing Telegram flow and includes a local-only test bot:

- Button-based goal selection.
- Button-based belief-mode selection.
- Rhythm selection.
- In-memory profile storage.
- First ritual response.
- No live webhook configuration.
- No production database writes.
- No real notification scheduling in the local test harness.

### Phase 2A — connected web profile and ritual flow

Commit `563bbc4` added the first connected backend flow:

- `ProfileRepository` in memory.
- Profile request validation.
- Profile creation and retrieval endpoints.
- Deterministic daily ritual selection.
- Free/Premium constraints.
- Dashboard ritual loading.
- Onboarding save action.
- Dedicated endpoint tests.

Commit `301341a` added the latest Hark screenshot-audit fixes:

- No belief mode preselected on onboarding.
- Next button disabled until a mode is selected.
- Improved Urdu, onboarding, dashboard label, and sidebar icon contrast.
- Added sidebar bottom padding so “Leave preview” remains visible.

## 4. Current architecture

```text
                    +-----------------------------+
                    |       React/Vite frontend    |
                    |-----------------------------|
                    | Landing                      |
                    | Onboarding                   |
                    | Dashboard                    |
                    | Tarot reflection preview     |
                    +--------------+--------------+
                                   |
                         relative HTTP API calls
                                   |
                    +--------------v--------------+
                    |       FastAPI POC backend    |
                    |-----------------------------|
                    | /health                      |
                    | /api/profile                 |
                    | /api/ritual/today           |
                    | /api/entitlement             |
                    | OpenAPI /docs                |
                    +------+-----------------------+
                           |
             +-------------+--------------+
             |                            |
+------------v-----------+    +-----------v------------+
| In-memory profile repo |    | In-memory entitlement   |
| UserProfile records    |    | plan/feature records    |
+------------+-----------+    +-----------+-------------+
             |                            |
             +-------------+--------------+
                           |
                 catalog ritual picker
                           |
              28 in-memory catalog rituals

Existing parallel product surface:

+-------------------------+
| Python Telegram bot     |
| onboarding, quests,     |
| rewards, streaks        |
+-------------------------+
```

### Repository responsibilities

- `app/bot/`: Telegram commands, handlers, and local test bot.
- `app/services/`: existing Telegram/application business logic.
- `app/models/`: domain model area for the existing application.
- `app/db/`: existing Supabase integration boundary; not used by the new web POC flow.
- `web-poc/frontend/src/main.jsx`: React route/view composition and mock/product-preview UI.
- `web-poc/frontend/src/styles.css`: visual system and responsive layout.
- `web-poc/backend/main.py`: FastAPI app and POC endpoints.
- `web-poc/backend/profile_service.py`: in-memory profile repository, catalog representation, and deterministic ritual selection.
- `web-poc/backend/entitlements.py`: plan definitions, feature limits, repository protocol, and in-memory entitlement implementation.
- `seeds/fortunis8_catalog.json`: structured catalog source.
- `seeds/fortunis8_catalog_seed.sql`: database seed artifact.
- `supabase/migrations/20261025000000_ritual_platform.sql`: ritual/profile schema artifact.
- `supabase/migrations/20261026000000_subscriptions.sql`: subscription/entitlement schema artifact.
- `tests/`: existing Telegram/service tests plus web entitlement and profile/ritual tests.

## 5. Current API surface

### `GET /health`

Returns a simple unauthenticated readiness response:

```json
{
  "status": "ok",
  "message": "FastAPI backend is online."
}
```

### `POST /api/profile`

Creates or replaces an in-memory user profile and returns an assigned ritual.

Accepted profile fields:

- `user_id`: temporary POC identity field.
- `goals`: unique catalog goal keys.
- `belief_mode`: `Scientific`, `Mindfulness`, `Spiritual`, `Religious`, `Practical`, or `Mixed`.
- `rhythm_minutes`: `2`, `5`, or `10`.
- `language`: `en` or `ur`.
- `optional_readings`: boolean.
- `delivery_time`: optional string.
- `timezone`: optional string.

Current entitlement checks:

- Free users may select at most two goals.
- Free users cannot select `Mixed` mode.
- Free users cannot select ten-minute rituals.

### `GET /api/profile?user_id=...`

Retrieves the in-memory profile. Returns `404` when no profile exists.

### `GET /api/ritual/today?user_id=...`

Returns the profile plus one deterministic ritual selected from the catalog using:

1. User-selected goals.
2. User-selected belief mode mapped to a catalog guidance mode.
3. Maximum ritual duration.
4. Practical fallback when the selected mode has no matching ritual.
5. A stable hash of user ID and calendar date.

Every returned ritual includes an explicit action step.

### `GET /api/entitlement?user_id=...`

Returns the current plan, `is_premium`, limits, features, and repository source. The current source is intentionally `in-memory-entitlements-repository`.

### Generated documentation

FastAPI exposes:

- `/openapi.json`
- `/docs`
- `/redoc`

The current response schemas are generic dictionaries. Typed response models should be added during the authenticated MVP phase.

## 6. Product behavior currently demonstrated

### Landing page

The landing page communicates:

- Mystical/personalized self-discovery positioning without supernatural guarantees.
- Daily rituals and action quests.
- User-selected belief flexibility.
- Optional readings.
- Science-informed principles.
- English and Urdu core concepts.
- Telegram-first entry point.
- Free and Premium plan previews.

### Onboarding

The user selects through UI controls rather than free-text entry:

1. Goals.
2. Guidance/belief mode.
3. Current state.
4. Rhythm and delivery preview.
5. Review.
6. Save profile and receive the first ritual.

No mode is selected by default. The mode step cannot proceed until the user explicitly chooses one.

### Dashboard

The dashboard preview includes:

- Greeting and path summary.
- Diamonds.
- Streak.
- Level and XP progress.
- Daily ritual card.
- Ritual completion interaction.
- Quest progress.
- Optional reading state.
- History preview.
- Profile/settings navigation.
- Premium upsell.

The current completion interaction is UI-local only. It does not yet persist completion or award rewards server-side.

### Reading page

The tarot page is currently a symbolic reflection preview. It explicitly avoids predictive or guaranteed-outcome claims and uses a dark glassy/card-based visual language with constellation imagery and energy rings.

## 7. Verified evidence

Latest validation on `manus-sync`:

- Full pytest suite: **39 passed, 0 failed**.
- Vite production build: **passed**.
- `/`: HTTP 200.
- `/onboarding`: HTTP 200.
- `/dashboard`: HTTP 200.
- `/reading/tarot`: HTTP 200.
- `/health`: HTTP 200.
- `/manus-routes.json`: HTTP 200 and valid JSON.
- Profile creation and daily ritual retrieval flow: verified.
- OpenAPI route presence verified for profile, ritual, and entitlement endpoints.
- Working tree clean.
- Local HEAD equals `origin/manus-sync`.

The full test suite currently emits six warnings from existing dependency/user-warning paths; they do not fail the suite.

## 8. What is intentionally not implemented yet

The following are known boundaries, not accidental omissions:

- No live Supabase migration execution.
- No production Supabase connection for the new web POC.
- No browser authentication or secure session identity mapping.
- No RLS policies applied or verified against a live database.
- No durable profile or ritual persistence in the web POC.
- No production notification scheduler.
- No email/push/Telegram delivery automation based on the web profile.
- No server-side ritual completion endpoint.
- No server-side XP, diamonds, levels, streak, quest, or reward transaction flow for the web app.
- No reading history persistence.
- No AI reflection generation in the web POC.
- No real payment checkout or webhook integration.
- No production subscription entitlement lookup.
- No public deployment.
- No mobile native application; mobile app remains the final product stage.

## 9. Prioritized remaining work

### P0 — security and persistence foundation

1. Confirm the final profile and subscription schema with the database owner.
2. Review the committed migrations without running them automatically.
3. Apply migrations only through the approved Supabase deployment process.
4. Implement authenticated user identity from Supabase Auth/session claims.
5. Remove trust in request-supplied `user_id` for browser routes.
6. Add profile tables/repository backed by Supabase.
7. Add RLS policies for profile, goals, preferences, and user-owned records.
8. Add typed API request and response models.

### P1 — daily product loop

1. Implement `PUT/PATCH /api/profile/me` using authenticated identity.
2. Implement `GET /api/profile/me`.
3. Implement persistent ritual assignment or a reproducible assignment record.
4. Implement `POST /api/ritual-completions`.
5. Make completion idempotent by user, ritual, and date.
6. Add server-side XP, diamonds, streak, level, and quest transactions.
7. Add history endpoints.
8. Add notification preferences, delivery time, and timezone validation.
9. Connect a scheduler/worker to deliver daily rituals through Telegram and future web channels.

### P1 — Telegram/web continuity

1. Define account-linking strategy between Telegram identity and web Auth identity.
2. Keep linking optional unless required by the notification experience.
3. Ensure Telegram and web use the same profile, ritual, completion, and progression repositories.
4. Preserve the existing Telegram behavior and regression suite.

### P2 — readings and personalization

1. Persist optional reading preferences.
2. Add reading request/result/history APIs.
3. Add clear safety/guardrail copy for readings.
4. Add AI reflection only behind an explicit entitlement and service boundary.
5. Add full bilingual content support and translation review.

### P2 — Premium and commercial integration

1. Replace the in-memory entitlement repository with the approved subscription tables/view.
2. Add payment-provider checkout and webhook handling.
3. Make webhook processing idempotent.
4. Verify trial, active, canceled, expired, and period-end behavior.
5. Keep the product promise explicit: Premium adds depth and convenience; it does not guarantee better fortune or outcomes.

### P3 — release and operations

1. Define production deployment topology for React/static assets plus FastAPI routes.
2. Add environment and secret management.
3. Add structured logs, metrics, error reporting, and health/readiness separation.
4. Add rate limiting and abuse controls.
5. Add backup/recovery and migration rollback procedures.
6. Add end-to-end authenticated staging tests.
7. Obtain approval before public publication.

### Final stage — mobile application

The native mobile app should follow the stable authenticated web MVP. It should reuse the API, profile model, ritual catalog, notifications, entitlement system, and progression services rather than introduce a separate product logic path.

## 10. Architectural decisions to preserve

- **Template-first onboarding:** avoid requiring users to write free-form personal descriptions for the core flow.
- **User-chosen belief mode:** never infer religious, spiritual, scientific, or other belief preferences.
- **Belief-flexible product boundary:** readings are optional and symbolic; the growth loop works without readings.
- **Science-informed claims:** use evidence-informed habit, attention, reflection, and implementation-intention language without medical or guaranteed claims.
- **Small actionable rituals:** every ritual ends with a concrete action step.
- **Catalog-driven behavior:** goals and rituals should remain data-driven rather than hard-coded into UI flows.
- **Entitlement at the service boundary:** Premium checks must be server-side and derived from the subscription source of truth.
- **Telegram preservation:** existing bot behavior and tests must remain intact as web functionality is added.
- **No production side effects during POC work:** migrations, live Supabase writes, payments, and live bot polling require explicit deployment-stage approval.
- **Mobile last:** stabilize the web/API product loop before native app development.

## 11. Recommended next checkpoint

The next implementation checkpoint should be a focused **authenticated profile MVP**:

1. Add Supabase Auth/session identity mapping.
2. Add typed `/api/profile/me` read/write endpoints.
3. Add repository interfaces with a test in-memory implementation and a production Supabase implementation boundary.
4. Add RLS-aware profile persistence after database-owner approval.
5. Keep ritual assignment deterministic and catalog-driven.
6. Add no production migration execution until the owner explicitly approves the deployment step.
7. Preserve the current 39-test baseline and add endpoint tests for authenticated ownership and cross-user access denial.

This is the smallest next step that converts the current connected POC into a secure, persistent MVP foundation without prematurely implementing payments, native mobile, or the complete notification platform.


## 10. Phase 2B authenticated MVP addendum

The repository has now advanced from Phase 2A into the authenticated MVP foundation. The active branch remains `manus-sync`; no changes were made to `main` or `prod-readiness-audit`.

Completed in this increment:

- Added strict bearer-token verification in `web-poc/backend/auth.py`. The server validates JWT signature, required claims, audience, optional issuer, expiry, issued-at, and subject. Missing credentials return 401; missing server auth configuration is explicit rather than silently accepting a user ID.
- Replaced browser-supplied ownership parameters with authenticated routes: `GET/PUT /api/profile/me`, `GET /api/ritual/today`, `POST /api/ritual-completions`, and `GET /api/entitlement/me`.
- Added typed Pydantic transport contracts and OpenAPI bearer security metadata.
- Added `SupabaseProfileRepository` as a server-side adapter using the verified auth subject and a service-role client only on the backend. The default test mode remains in memory.
- Added server-authoritative, idempotent ritual completion responses with XP/diamond awards in the local repository boundary.
- Added browser Supabase session restoration, sign-up, sign-in, sign-out, protected routes, authenticated API headers, and explicit unavailable/error states. No fake demo authentication is exposed.
- Added the unapplied `supabase/migrations/20261102000000_phase2b_auth_mvp.sql`. It makes `telegram_id` nullable for web-only accounts and adds owner RLS policies. It was validated only against a disposable local PostgreSQL database; no live Supabase SQL was executed.

Validation evidence for this increment: 46 pytest tests pass, the Vite build passes, the route manifest includes `/login` and `/signup`, the static security checks pass, and the complete migration chain applies to the disposable local PostgreSQL database when Supabase-like roles/functions are stubbed locally.

Remaining production gates: Hark/database owner review and application of the migrations, Supabase browser/server environment configuration, enabling `WEB_POC_PROFILE_REPOSITORY=supabase`, replacing in-memory completion/progression with durable transactional ledgers, notification scheduling, payment webhooks, and production deployment approval.
