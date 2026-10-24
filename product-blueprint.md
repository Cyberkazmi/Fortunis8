# Fortunis8 Customer-Facing Product Blueprint

## Purpose and product promise

Fortunis8 is a personalized daily ritual for reflection, guidance, and playful progression. It combines a user's zodiac identity, mood, persona, daily fortune, tarot and horoscope readings, quests, diamonds, and streaks in one calm celestial experience.

Primary value proposition:

> **A daily moment of insight shaped around who you are feeling like today.**

Primary call to action: **Begin your reading**.

Secondary call to action: **Explore the ritual**.

This blueprint describes the intended consumer product. It does not claim that these pages are implemented in the current POC or backend.

---

## Product hierarchy

```text
Public
├── Landing /
├── Login /login
├── Sign up /signup
└── Password / recovery states

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

Primary authenticated navigation is a compact bottom navigation on mobile and a left rail on desktop:

```text
Today     Read     Quests     History     Profile
```

The diamond balance and streak are always visible in the authenticated shell. The active page is identified by both color and label, never color alone.

---

## Core user journeys

### First visit to first insight

A visitor lands on the public page, understands that Fortunis8 creates personalized daily readings, and selects **Begin your reading**. They enter the signup flow, choose a login method, and are guided through a short personalization sequence: zodiac sign or birth information, preferred persona, and current mood. After saving, they arrive at the dashboard with a first daily insight prompt.

Existing capability: persona and mood normalization, profile onboarding concepts, horoscope/fortune generation services, and Telegram onboarding behavior.

Required new work: browser authentication, authenticated profile ownership, web onboarding routes, browser-safe API contracts, and secure persistence of the web identity.

### Returning daily ritual

An authenticated user opens Today and sees their greeting, current persona, mood, zodiac profile, streak, diamond balance, daily quest progress, and the next suggested action. They claim the daily reward, then choose a daily fortune, tarot, or horoscope reading. The completed reading is saved to history and contributes to relevant quest progress.

Existing capability: daily reward calculation, streak calculation, diamonds and levels, quest matching/completion logic, and AI reading generation paths.

Required new work: authenticated HTTP endpoints, idempotent server-side reward claims, reading persistence, reward ledger persistence, and browser UI integration.

### Explore a reading

The user enters Reading center, chooses Daily fortune, Tarot, or Horoscope, optionally supplies a question for tarot, and starts the reading. The UI shows a short preparation state, then presents a result card with the reading, reading type, creation time, and actions to save, share, or return to Today.

Existing capability: horoscope, tarot, palm-reading prompt construction and OpenAI generation helpers.

Required new work: web request validation, rate limits/usage policy, authenticated generation endpoints, durable reading records, failure/retry states, and share behavior.

### Build momentum through quests

The user opens Quests, sees available, active, and completed quests, and selects a quest to understand its reward and progress. Completing a qualifying action updates progress and awards diamonds once. Rewards shows the current diamond balance, level, recent reward events, and streak milestones.

Existing capability: local quest detection/completion, diamond awarding, and level calculation.

Required new work: authoritative server-side quest progress, duplicate-safe completion, reward event history, API ownership checks, and database policies.

### Personalize the experience

The user opens Profile, reviews their public-facing identity and zodiac information, then opens Personalization to change persona and mood. Changes are previewed, explicitly saved, and reflected in the next generated reading.

Existing capability: profile normalization and update helpers, persona options, mood options, and Telegram personalization handlers.

Required new work: browser profile API, auth-user-to-profile mapping, validation/error handling, and Supabase row-level ownership enforcement.

---

## Page-by-page product blueprint

### 1. Public landing page `/`

**Purpose:** Explain Fortunis8 quickly and convert a curious visitor into a reader.

**Visible components:**

- Celestial navy background with restrained star field.
- Wordmark and a minimal top navigation: How it works, Sign in.
- Hero statement: “A daily moment of insight shaped around who you are feeling like today.”
- Primary CTA: **Begin your reading**.
- Secondary CTA: **See how it works**.
- Three compact benefit modules: Personalized readings, Rituals that build momentum, Your story over time.
- A product preview strip showing a dashboard card, reading result card, and streak/quest card using clearly labeled preview data.
- A short trust boundary: “Your readings are personal. Your account controls your profile.”
- Footer links for privacy, terms, and sign in.

**Main actions:** Begin signup, sign in, view product explanation.

**Current support:** None in the current POC beyond a visual technical landing surface.

**New work:** Marketing copy/layout, responsive public route, metadata/SEO, real auth links, and production content review.

### 2. Login and signup `/login`, `/signup`

**Purpose:** Establish a real authenticated browser session.

**Visible components:**

- Fortunis8 mark and concise welcome message.
- Email/password or selected provider form, depending on the approved Supabase Auth configuration.
- Loading, invalid credentials, expired link, and retry states.
- Link between login and signup.
- Password recovery state.
- Privacy/terms acknowledgement where required.

**Main actions:** Create account, sign in, recover access, return to landing page.

**Current support:** No browser authentication exists. The Telegram bot identifies users through Telegram context, not browser identity.

**New work:** Supabase Auth setup, secure token/session handling, callback handling, protected routes, logout, and auth-user-to-profile mapping.

### 3. Authenticated dashboard `/app`

**Purpose:** Make the daily ritual immediately understandable and actionable.

**Visible components:**

- Greeting using the profile name or chosen display name.
- Identity chip: zodiac sign, persona, and current mood.
- Daily insight card with a short preview and CTA **Reveal today's fortune**.
- Daily reward/streak card showing current streak, next milestone, and **Claim reward** state.
- Diamond balance and level indicator.
- Quest rail with one featured quest and progress.
- Quick actions: Daily fortune, Tarot, Horoscope.
- Recent reading card with a link to history.
- Persistent bottom navigation on mobile.

**Main actions:** Claim daily reward, start a reading, open quests, edit personalization, view history.

**Current support:** Profile fields, diamonds, levels, quests, streak calculation, and reading generators exist in backend code paths; no web dashboard API exists.

**New work:** `/api/me`, `/api/streak`, `/api/quests`, `/api/readings`, `/api/rewards`, authenticated dashboard composition, and browser state management.

### 4. Reading center `/app/read`

**Purpose:** Let users choose the kind of insight they want without overwhelming them.

**Visible components:**

- Page title: “What are you listening for?”
- Three reading cards:
  - Daily fortune: a concise guidance ritual.
  - Tarot: a question-led draw.
  - Horoscope: zodiac-focused perspective.
- Optional tarot question input.
- Persona and mood context shown as editable chips.
- Estimated preparation/loading state.
- Clear usage/failure message if generation is unavailable.

**Main actions:** Choose reading type, enter a tarot question, generate reading, return to Today.

**Current support:** Fortune, tarot, horoscope generation helpers and AI service integration exist.

**New work:** Authenticated web endpoints, request validation, usage/rate policy, UI loading and failure states, reading persistence, and abuse protection.

### 5. Reading result `/app/readings/:id`

**Purpose:** Make a generated reading feel meaningful, readable, and worth returning to.

**Visible components:**

- Reading type, date, zodiac/persona/mood context.
- Strong editorial reading title.
- Reading body with clear paragraph rhythm.
- Optional “What to carry today” takeaway.
- Actions: Save/bookmark, share/copy, generate another, return to Today.
- Related quest progress if the reading completed a quest.
- Error state if the reading cannot be loaded.

**Main actions:** Read, save, share, generate another reading, go to history.

**Current support:** Generated text can be produced, but reading results are not currently exposed through a browser route or consistently persisted to `fortune_readings`.

**New work:** Reading record creation, secure retrieval by authenticated owner, history linkage, share policy, and result UI.

### 6. Reading history `/app/history`

**Purpose:** Turn isolated readings into a personal archive.

**Visible components:**

- Timeline grouped by date.
- Filters for fortune, tarot, and horoscope.
- Search or lightweight keyword filtering after the MVP.
- Reading cards with type, date, title, and excerpt.
- Empty state for a new account.
- Pagination or infinite loading when history grows.

**Main actions:** Filter, reopen a reading, delete or archive where supported.

**Current support:** The SQL schema includes a `fortune_readings` table, but the current Telegram generation path does not provide a verified complete history workflow.

**New work:** Persist readings, owner-scoped list/detail endpoints, indexes/pagination, deletion policy, and UI states.

### 7. Quests `/app/quests`

**Purpose:** Give the user a clear progression loop beyond reading generation.

**Visible components:**

- Tabs or filters: Active, Available, Completed.
- Quest cards with title, description, progress, reward, and completion state.
- Featured quest at top.
- Diamond reward preview.
- Completion confirmation and duplicate-safe disabled state.

**Main actions:** Inspect quest, perform the qualifying action, claim or receive completion reward, view reward history.

**Current support:** Quest listing, local matching, and completion logic exist.

**New work:** Authoritative persistence, progress API, duplicate protection, ownership/RLS, and web event integration.

### 8. Rewards `/app/rewards`

**Purpose:** Make progress and earned value legible.

**Visible components:**

- Current diamonds and level.
- Progress bar to next level.
- Streak milestone panel.
- Recent reward events with reason and date.
- Reward explanation: daily claim, quest completion, other future sources.
- Empty state for a new user.

**Main actions:** Claim daily reward when available, inspect reward history, return to quests or Today.

**Current support:** Diamond arithmetic, level calculation, welcome reward, and daily reward logic exist.

**New work:** Reward ledger persistence, authenticated reward API, idempotency, and UI history.

### 9. Profile `/app/profile`

**Purpose:** Let the user understand and control their identity in Fortunis8.

**Visible components:**

- Display name and avatar/initial.
- Zodiac sign and birth information summary.
- Persona and mood summary.
- Account email/auth provider indicator.
- Links to Personalization, security, privacy, and logout.
- Account deletion/export placeholder until implemented.

**Main actions:** Edit personalization, sign out, manage account.

**Current support:** Telegram profile creation, persona, mood, zodiac-related profile fields, and profile update helpers exist.

**New work:** Browser identity mapping, profile API, settings persistence, auth/security surfaces, and privacy/account lifecycle actions.

### 10. Personalization `/app/profile/personalize`

**Purpose:** Make future readings feel intentionally personal.

**Visible components:**

- Persona selection cards.
- Mood selection cards.
- Zodiac/birth information editor.
- Live “your readings will feel…” preview copy.
- Save and cancel actions.
- Unsaved-change warning.

**Main actions:** Change persona, change mood, update zodiac details, save.

**Current support:** Persona/mood option lists, normalization, and Telegram handlers exist.

**New work:** Authenticated browser form, validation, secure persistence, optimistic/loading states, and API tests.

---

## Visual system

The existing navy/gold celestial language is retained, but the product shifts from technical status demo to warm consumer ritual.

### Palette

- **Ink navy:** primary background and navigation foundation.
- **Deep indigo:** elevated cards and dashboard surfaces.
- **Warm parchment:** main reading text and editorial surfaces.
- **Celestial gold:** primary CTA, active progress, diamonds, and highlights.
- **Soft mint:** healthy connection, completed quest, and positive confirmation.
- **Rose ember:** error, caution, and destructive states only.
- **Muted blue-gray:** secondary text and inactive navigation.

Gold should signal invitation and progress, not decorate every component. Mint should communicate success rather than act as a second brand color.

### Typography

- Serif display face for major emotional headlines and reading titles.
- Compact sans-serif for controls, metadata, status, and navigation.
- Reading body text uses a comfortable measure and generous line-height.
- Headings are editorial and specific; avoid generic product phrases.

### Components

- Bottom navigation on mobile; left rail on desktop.
- Rounded but not inflated cards, with one clear focal card per screen.
- Status pills for streak, diamonds, and connection states.
- Gold primary buttons with clear verbs.
- Empty states that explain the next meaningful action.
- Skeleton/loading states that preserve page structure.
- Every destructive or irreversible action requires explicit confirmation.

### Motion

Motion is restrained: short page entrance, subtle card lift on interaction, progress transitions, and reading reveal. Avoid floating starfield animation or excessive shimmer that would compete with the reading content. Respect reduced-motion preferences.

---

## Existing capabilities versus required work

| Product capability | Existing code | Verified today | New web/API/database work required |
|---|---|---|---|
| Telegram onboarding | Yes | CI/unit tests | No web equivalent yet |
| Persona options and normalization | Yes | Tests and Telegram flow | Authenticated profile API/UI |
| Mood options and normalization | Yes | Tests and Telegram flow | Authenticated profile API/UI |
| Zodiac/profile fields | Partial | Code-level only | Auth-user mapping and web persistence |
| Fortune generation | Yes | Mocked AI tests | Authenticated endpoint, limits, persistence |
| Tarot generation | Yes | Code-level path | Authenticated endpoint, question validation, persistence |
| Horoscope generation | Yes | Code-level path | Authenticated endpoint, persistence |
| Diamonds/levels | Yes | Reward tests | Server-authoritative web API and ledger |
| Daily reward/streak | Yes | Integration tests and CI | Idempotent authenticated endpoint and streak history |
| Quests | Yes | Local integration tests and CI | Durable progress, API, RLS, web event hooks |
| Reading history | Schema exists | Not end-to-end verified | Persist/read/delete API and UI |
| Supabase client | Yes | Lazy-client tests | Supabase Auth and secure profile ownership |
| FastAPI health/readiness | Yes | CI and POC checks | Production container and expanded API |
| Browser login/signup | No | No | Supabase Auth/session/callback implementation |
| Public landing page | POC technical surface only | Mobile screenshot | Consumer copy, SEO, final route |
| Dashboard/readings/quests UI | No | No | React application build |

---

## Login and state model

The public shell has four states: anonymous landing, signup, login, and recovery. The authenticated shell has loading, authenticated, expired-session, and logged-out states. Every protected page should show a stable loading skeleton while auth is resolving; it must not briefly render a false logged-out or false user state.

For the first web MVP, Supabase Auth is the intended provider. The minimum safe data model adds an `auth_user_id` ownership field to profiles and applies row-level policies so the authenticated user can only read and mutate their own profile, readings, rewards, streaks, and quest progress. Client-supplied Telegram IDs remain untrusted and are not used as browser identity.

Telegram account linking is intentionally excluded from the initial web MVP. It can be designed later as an explicit, server-generated linking flow if cross-channel continuity becomes a validated product requirement.

---

## Proposed v0 preview boundary

Before full integration, the next visual preview should replace the technical connectivity demo with two static, clearly labeled product screens using mock data only:

1. **Landing v0:** value proposition, primary CTA, three benefit modules, and a product preview strip.
2. **Dashboard v0:** mock authenticated state showing persona, mood, zodiac, daily insight, diamonds, streak, quest progress, and quick reading actions.

The v0 should not call Supabase, OpenAI, Telegram, or production APIs. It should use fixture data labeled as preview data. Its purpose is to approve the customer-facing hierarchy, density, and tone before any authenticated API integration begins.

### Design checkpoint

The chosen design system is the retained navy/gold celestial language transformed into a compact mobile ritual: editorial serif headlines, warm reading surfaces, indigo cards, gold invitations, mint confirmations, and restrained motion. The v0 should be reviewed for hierarchy and tone before the complete application is built.
