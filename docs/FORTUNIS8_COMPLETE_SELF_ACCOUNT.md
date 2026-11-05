# Fortunis8 Complete Self-Account

**As of:** 2026-11-05
**Repository:** `Cyberkazmi/Fortunis8`
**Active branch:** `manus-sync`
**Current HEAD:** `5ed4116007d89c39f31f456cd9ccb772a9cbd439`
**Branch state:** Clean and aligned with `origin/manus-sync`
**Current phase:** Phase 2B — authenticated MVP foundation, with persistence and production operations still gated

## Executive summary

Fortunis8 began as an existing Telegram application with daily rewards, streaks, quest logic, profile concepts, OpenAI-backed reading paths, and a Supabase integration boundary. The project direction then expanded into a broader product: a science-informed, belief-flexible daily growth platform where users select goals and guidance preferences through templates, receive personalized rituals, complete quests, earn progression rewards, and optionally use tarot, horoscope, fortune, or palm prompts as reflective experiences rather than guaranteed predictions.

The work progressed in deliberate stages. First, the production-readiness baseline and Telegram behavior were stabilized. Next, a product blueprint and isolated Web POC transformed the technical connectivity demo into a consumer-facing landing page, onboarding flow, dashboard, reading preview, premium preview, and mobile-oriented visual system. Then the catalog and schema were expanded for 13 goals, multiple guidance modes, bilingual rituals, subscriptions, and entitlements. A local Telegram test bot proved button-based onboarding and quest progression. The web POC then connected React to FastAPI for profile creation and deterministic daily ritual assignment.

The latest increment moved the project from a user-ID-based web POC to an authenticated MVP foundation. Supabase-compatible JWT verification now derives ownership from the token subject; protected `/me` APIs use typed contracts; a server-side Supabase profile adapter exists; ritual completion has an idempotent server boundary; and the React frontend includes Supabase session restoration, sign-up, sign-in, logout, protected routes, and explicit unavailable/error states. The migration is committed but unapplied to live Supabase by design.

This is not yet a production SaaS. Durable profile/progression storage, live RLS execution, notification scheduling, reading persistence, payment webhooks, production entitlement lookup, deployment, and the native mobile app remain future gates.

## 1. Original starting point and baseline work

The repository already contained the Fortunis8 Telegram application and a Python service architecture. The early work was not a rewrite. It preserved the existing bot and tests while fixing production-readiness issues and creating a safer base for product expansion.

The baseline work included resolving the `python-telegram-bot` and `httpx` dependency conflict, correcting startup validation so a missing `TELEGRAM_BOT_TOKEN` raises the intended `RuntimeError` instead of `telegram.error.InvalidToken`, and fixing test isolation around Supabase client state. Quest and streak integrations were wired into the Telegram application, and the production-readiness audit reached a stable candidate state.

A malformed Git tree entry involving a pathname containing `app/services/rewards_service.py` followed by a newline and embedded Python source was investigated and removed only where appropriate, while preserving the legitimate service file. The repository was synchronized from the healthy `main` baseline rather than treating an empty `git clone --no-checkout` working tree as deletions. Work was kept on the requested development branch and never redirected into `main` or `prod-readiness-audit`.

Important baseline commits visible in the current history include:

- `1344150` — align `httpx` with `python-telegram-bot`.
- `57aceb3` — validate Telegram configuration before application construction.
- `3772ac0` — reset Supabase state after startup tests.
- `2d553e5` — wire daily streak rewards into Telegram.
- `518a92f` — merge the Telegram daily streak baseline used for product expansion.

## 2. Product direction and blueprint

The approved product promise became:

> Fortunis8 is a personalized daily ritual for reflection, guidance, and playful progression.

The blueprint deliberately broadens the audience beyond one reading category. The product should work for someone pursuing business wealth, exam success, a job interview, health and energy, calm, relationships, creativity, discipline, spiritual reflection, a religious routine, confidence, a life transition, or sleep recovery. A user selects a goal and a guidance mode rather than being forced into a single worldview.

The key design decision is belief flexibility without belief inference. A user may choose Scientific, Mindfulness, Spiritual, Religious, Practical, or Mixed guidance. The system must not infer a person’s religion, spirituality, or skepticism from their goals or behavior. The daily growth loop must work without readings; readings remain optional, symbolic, and framed as reflection prompts. Scientific language is allowed for habit formation, attention, reflection, implementation intentions, and neuroplasticity-informed behavior change, but the product must not make medical, supernatural, or guaranteed-outcome claims.

The blueprint hierarchy is:

```text
Public
├── Landing /
├── Login /login
├── Sign up /signup
└── Password recovery states

Authenticated app
├── Dashboard /app
├── Reading center /app/read
│   ├── Daily fortune /app/read/fortune
│   ├── Tarot /app/read/tarot
│   └── Horoscope /app/read/horoscope
├── Reading result /app/readings/:id
├── Reading history /app/history
├── Quests /app/quests
├── Rewards /app/rewards
├── Profile /app/profile
└── Personalization /app/profile/personalize
```

The intended authenticated navigation is Today, Read, Quests, History, and Profile, with diamonds and streak always visible. The intended customer flow is landing page to signup/login, template personalization, dashboard, daily ritual, optional reading, quests, rewards, history, and profile settings.

The blueprint also explicitly distinguished existing backend capability from required web/API/database work. Existing code included Telegram onboarding, persona and mood normalization, reading-generation helpers, reward arithmetic, quest logic, streak logic, and Supabase client boundaries. Required work included browser authentication, auth-user-to-profile mapping, typed API contracts, secure persistence, RLS, reading persistence, reward ledgers, notification scheduling, payment integration, and mobile delivery.

## 3. Phase 1 — product blueprint and isolated Web POC

The first web request was intentionally constrained: prove that a React frontend and Python/FastAPI backend could coexist without using production credentials, Supabase, OpenAI readings, Telegram, or database writes. The smallest useful proof was a mobile-sized React UI served alongside a FastAPI `/health` endpoint.

The initial technical connectivity demo was not accepted as the customer experience. It contained backend-oriented copy such as “The room is open,” “Backend Signal,” and “React → /health → FastAPI.” The product requirement changed the work from cosmetic restyling to a real consumer-facing experience.

The POC was redesigned to include:

- a public landing page with value proposition and primary CTA;
- template-based onboarding rather than free-form input;
- a dashboard preview with greeting, persona/mood/zodiac summary, daily insight, diamonds, streak, levels, XP, quests, and reading entry points;
- tarot, horoscope, fortune, and palm reflection previews;
- history, rewards, profile, and premium-preview surfaces;
- mobile-first layout and bottom navigation;
- English and Urdu core concepts;
- explicit preview/mock boundaries.

The visual system evolved during the work. The first approved direction retained midnight navy and restrained gold celestial styling. Later Hark screenshot review requested a bright deep sky-blue landing/application theme with darker reading surfaces, glassy rounded reading cards, constellation imagery, energy rings, a centered serif landing headline, gold italic script, smoky reveal treatment, and reduced-motion support. The final POC reflects that later direction: bright sky-blue on landing and app surfaces, darker contrast on reading pages, premium pricing copy, dashboard upsell, and explicit “not guaranteed outcomes” language.

## 4. Phase 1B — catalog, schema, and entitlement design

The product model was expanded additively rather than by rewriting the existing MVP schema. The catalog contains 13 goal paths:

1. `business_wealth`
2. `study_exams`
3. `career_interview`
4. `health_energy`
5. `stress_calm`
6. `relationships`
7. `creativity`
8. `discipline`
9. `spiritual_reflection`
10. `religious_routine`
11. `confidence`
12. `life_transition`
13. `sleep_recovery`

The seed artifacts include structured JSON, SQL seed data, a catalog build script, bilingual English/Urdu draft content, guidance modes, current-state values, optional traditions, and 28 draft rituals tagged by goal and guidance mode. Every ritual is designed to end with a concrete action step. The seed rituals remain draft/inactive until the catalog owner approves them.

Subscription and entitlement work introduced exact plan keys and service-boundary checks. Free includes one daily ritual, up to two goals, one guidance mode, basic XP/levels/streaks/diamonds, one simple reading per day, seven-day history, and the basic progression loop. Premium pricing was specified as PKR 499/month or PKR 3,999/year and $4.99/month or $39.99/year, with a seven-day trial. Premium adds broader goals and modes, deeper rituals and readings, AI reflection, full history/charts, streak freezes, custom reminders, premium quests, ad-free use, and early access. The copy explicitly states that Premium does not mean better fortune or guaranteed outcomes.

The entitlement implementation uses a repository interface with `get_plan_key`, `get_plan`, and `get_features`. The in-memory repository mirrors the intended `user_entitlements` view behavior: active or trialing subscriptions with a future period end are selected newest first; otherwise the user is Free. A future Supabase entitlement adapter exists as a boundary but deliberately does not connect in the POC.

Two Hark-authored migration files were committed unchanged for the ritual platform and subscription schema. A later Phase 2B migration was added for authenticated web profiles, nullable Telegram identity, and owner-scoped RLS policies. None of these migrations were run against live Supabase.

## 5. Phase 1C — Telegram onboarding and progression prototype

The existing Telegram behavior was preserved. A separate local-only test bot was added to prove the template-first onboarding direction without touching production Telegram configuration.

The local bot uses button-based choices for goals, belief mode, and ritual rhythm. It stores profiles in memory and returns a first ritual. It does not connect to Supabase, write real users, configure a webhook, schedule real notifications, or start a production bot. The production Telegram application and existing tests remain separate from this local harness.

This was important because the product direction is Telegram-first but not Telegram-only. Telegram remains an entry and notification surface, while the web application is the broader SaaS surface. Account linking was intentionally excluded from the initial web MVP until a real cross-channel dependency is validated.

## 6. Phase 2A — connected web profile and ritual flow

The first integrated product checkpoint connected the React POC to FastAPI. It added an in-memory `ProfileRepository`, typed profile validation, profile creation and retrieval, deterministic daily ritual assignment, free/premium constraints, onboarding save behavior, and dashboard ritual loading.

The ritual picker uses user-selected goals, the user-selected guidance mode mapped to catalog guidance, the maximum rhythm duration, a Practical fallback when no mode-specific ritual exists, and a stable hash of user ID and calendar date. The same user gets a deterministic choice for the same date, while the selection can change across dates. No belief mode is preselected; the onboarding Next button is disabled until the user explicitly chooses one.

Free limits are enforced at the API boundary: no more than two goals, no Mixed guidance, and no ten-minute ritual. Every response includes an explicit action step. This is catalog-driven behavior rather than UI-only hardcoding.

The visual audit fixes in `301341a` improved Urdu and onboarding contrast, dashboard gold labels, sidebar icons, and bottom padding so “Leave preview” is not hidden by the preview banner.

## 7. Phase 2B — authenticated MVP foundation

The latest major implementation increment is Phase 2B. It was developed from the existing POC instead of replacing it.

### Backend security and identity

`web-poc/backend/auth.py` adds strict Supabase-compatible bearer-token verification. The verifier checks signature, required claims, audience, optional issuer, expiry, issued-at, and a valid subject. Missing credentials produce a 401 Bearer challenge. If the server has no auth configuration, it produces an explicit unavailable state rather than silently accepting a browser-supplied ID.

The main security decision is that user ownership is derived from the verified token subject. The browser no longer supplies `user_id` to decide whose profile or ritual is being accessed. This prevents a caller from changing another user’s profile simply by changing a request parameter.

### Typed API boundary

Pydantic contracts were added for profile payloads, profile responses, rituals, entitlements, and completion responses. The protected web API is:

```text
GET  /api/profile/me
PUT  /api/profile/me
GET  /api/ritual/today
POST /api/ritual-completions
GET  /api/entitlement/me
```

`GET /health`, `/openapi.json`, `/docs`, and `/redoc` remain available for readiness and inspection.

### Persistence adapter

`SupabaseProfileRepository` provides the server-side adapter boundary. It uses the verified auth subject and a server-only service-role client when `WEB_POC_PROFILE_REPOSITORY=supabase` is explicitly configured. The default local/test mode remains in memory so tests and credential-free preview do not require a live database.

The browser receives only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. The service-role key and JWT verification secret belong only to the server environment. The repository never trusts browser-supplied service-role values or user IDs.

### Completion and rewards

`completion_service.py` adds an idempotent in-memory ritual completion boundary. The server confirms that the submitted ritual is the one assigned to the authenticated user for the current day, then returns a duplicate-safe completion record with XP and diamond awards. This is an MVP service boundary, not yet a durable transactional ledger.

### Frontend authentication

The React app now uses the official Supabase browser client when credentials are present. It restores sessions, supports sign-up/sign-in/sign-out, protects onboarding/dashboard/reading routes, attaches the bearer token to API requests, and displays explicit loading, unavailable, and backend-error states. It does not show fake demo success when credentials are absent.

The current web route set is:

```text
/
/login
/signup
/onboarding
/dashboard
/reading/tarot
/technical-poc
```

This is deliberately smaller than the final blueprint hierarchy. The full reading center, reading result/history, quests, rewards, profile, and personalization routes remain future work.

### Migration boundary

`supabase/migrations/20261102000000_phase2b_auth_mvp.sql` is committed source only. It makes Telegram identity optional for web-only profiles and adds owner-scoped RLS policies. It was syntax-validated against a disposable local PostgreSQL database with Supabase-like roles/functions stubbed locally. No live Supabase database was connected and no production migration was executed.

## 8. Challenges and how they were handled

### Repository and branch safety

The repository began from a no-checkout state and had a malformed tree-entry investigation in its history. The working tree was populated safely, existing changes were protected, and the active development branch was kept separate from `main` and `prod-readiness-audit`. Commits were kept small and included the requested Manus co-author attribution.

### Dependency and startup ordering

The `python-telegram-bot`/`httpx` conflict was resolved by aligning the dependency contract. Startup validation was moved before Telegram application construction so a missing token produces the intended application error rather than an SDK-level invalid-token exception.

### Test isolation

Supabase client state leaked between startup-import tests. The tests were corrected to reset client state after each test, preserving isolation without modifying production behavior.

### Product-direction correction

The first web surface was technically correct but product-wrong: it looked like a backend connectivity demo. The work was redirected toward an actual consumer product blueprint with meaningful product previews, template onboarding, dashboard progression, reading surfaces, premium framing, and explicit mock-data boundaries.

### Theme evolution

The visual language changed from the original navy/gold product blueprint to the later owner-requested sky-blue application surfaces with dark reading pages. The change was implemented as a visual-system update rather than changing the product’s core belief-flexible and science-informed boundaries.

### Preview/runtime drift

At one point the preview served an older process, so new routes returned 404 even though the source was correct. The stale process was stopped and the preview was restarted. The separate preview virtual environment then lacked the newly declared PyJWT dependency, producing `ModuleNotFoundError: jwt`. PyJWT was installed into that preview environment, after which the current routes served correctly. This distinction is why repository dependency declarations and runtime environment checks must both be validated.

### Documentation drift

The existing architect handoff was written during Phase 2A and still contains historical Phase 2A API descriptions and a 39-test snapshot in its earlier sections. The later Phase 2B addendum records the authenticated MVP changes and 46-test validation. The current self-account supersedes those historical sections and explicitly identifies the Phase 2B state.

## 9. Current verified status

The current branch is clean and aligned with `origin/manus-sync` at `5ed4116007d89c39f31f456cd9ccb772a9cbd439`. The latest implementation commit is `22fba68c4e92775846a2469af722a5d55a349404`, followed by documentation commits `3408cee` and `5ed4116`.

The final validation evidence for the authenticated MVP foundation is:

- Full Python suite: **46 passed**, 6 non-failing warnings.
- Vite production build: **passed**.
- Route manifest: valid JSON and includes `/login` and `/signup`.
- Preview routes: `/`, `/login`, `/signup`, `/onboarding`, `/dashboard`, `/reading/tarot`, `/health`, `/openapi.json`, and `/manus-routes.json` all returned HTTP 200 after the runtime restart.
- Unauthenticated `GET /api/profile/me`: correctly returned HTTP 401 with `Bearer access token required.`
- Migration chain: applied only to disposable local PostgreSQL for validation.
- Live Supabase: not connected; no live SQL executed.
- Live Telegram: not started; no webhook or production polling configured.
- Public deployment: not performed.

## 10. Blueprint pipeline adherence

| Blueprint stage | Intended outcome | Actual status | Assessment |
|---|---|---|---|
| Production-readiness baseline | Stable Telegram bot, config validation, tests, rewards/streaks | Completed before product expansion | On pipeline |
| Product blueprint | Customer-facing hierarchy, user journeys, visual system, separation of existing/new work | Completed in `product-blueprint.md` | On pipeline |
| Isolated Web POC | React + FastAPI hybrid, no production credentials or writes | Completed and validated | On pipeline |
| Consumer visual checkpoint | Landing, dashboard, onboarding, readings preview, mobile visual language | Completed as POC preview | On pipeline, but not production integration |
| Catalog/schema design | 13 goals, guidance modes, bilingual rituals, draft migrations, subscription shapes | Completed as source artifacts | On pipeline; database owner gate remains |
| Telegram onboarding prototype | Button-based template onboarding and progression proof | Completed locally | On pipeline; production notification automation remains |
| Connected web profile loop | Profile API, deterministic ritual assignment, free/premium enforcement | Completed with in-memory repository | On pipeline; persistence originally deferred |
| Authenticated MVP foundation | Supabase session, JWT verification, `/me` ownership, typed contracts, adapter, idempotent completion boundary | Completed in Phase 2B | On pipeline; durable database execution remains |
| Durable web product | Live Supabase persistence, RLS, reward ledger, history, readings, notifications, payments | Not completed | Correctly not skipped; next phase |
| Native mobile app | Reuse stable web/API product loop in mobile | Not started | Correctly deferred to final stage |

The work is following the blueprint pipeline. It has not overstepped into live migrations, production payments, public deployment, or mobile development. The only qualification is that the visual POC and authenticated MVP are not the complete consumer SaaS hierarchy yet; several blueprint routes are intentionally still absent.

## 11. What is complete versus what is not

### Complete and verified

- Existing Telegram application preserved.
- Telegram dependency and startup-readiness fixes.
- Streak, reward, quest, and onboarding test coverage preserved.
- Product blueprint and schema design artifacts.
- 13-goal catalog and 28 bilingual draft rituals.
- Sky-blue landing/application visual system and dark reading surfaces.
- Template-based onboarding with explicit mode selection.
- In-memory profile repository and deterministic ritual assignment.
- Free/premium entitlement rules and pricing copy.
- Local Telegram test bot.
- Authenticated Supabase browser session boundary.
- Server-side JWT verification and ownership derivation.
- Typed authenticated API contracts.
- Supabase profile repository adapter boundary.
- Idempotent local ritual completion response.
- 46 passing tests and successful Vite build.
- Repository-integrated architect handoff skill.

### Not complete or not production-enabled

- Live Supabase migration execution.
- Live RLS verification.
- Durable profile, ritual, completion, reward, quest, streak, and history storage.
- Real reading-generation web endpoints and persisted results.
- Full reading center, history, quests, rewards, profile, and personalization routes.
- Production notification scheduler and multi-channel delivery.
- Payment checkout, webhooks, and production subscription lookup.
- Public deployment and operational monitoring.
- Account linking between Telegram and web Auth.
- Native mobile application.

## 12. Recommended next sequence

1. Have the database owner review and explicitly approve the committed Phase 2B migration.
2. Apply it through the approved Supabase deployment process only.
3. Configure browser-safe Supabase values and server-only JWT/service-role values in the intended environment.
4. Enable the Supabase profile repository and verify ownership/RLS in staging.
5. Replace in-memory completion and entitlement state with durable, idempotent database transactions.
6. Add authenticated reading, history, quest, reward, streak, and notification APIs in small increments.
7. Add payment webhook synchronization only after the entitlement schema is live.
8. Run authenticated staging acceptance checks before publication.
9. Stabilize the web/API contract before beginning the native mobile stage.

## 13. Preview

The current local Webdev preview is listening on port 3000 and the health endpoint returned HTTP 200. The preview is not a public production deployment.

Preview routes:

- `/`
- `/login`
- `/signup`
- `/onboarding`
- `/dashboard`
- `/reading/tarot`
- `/technical-poc`

The preview should be described as an authenticated MVP foundation with credential-dependent auth behavior and local in-memory fallback, not as a live Supabase-backed production SaaS.
