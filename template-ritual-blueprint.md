# Fortunis8 Template Ritual Product Blueprint

## Product direction

Fortunis8 is a template-driven daily ritual and personal-growth companion. Users do not need to write a long intake form or explain themselves from scratch. They choose from clear, optional cards; those selections form an editable profile; the ritual engine uses that profile to recommend a small daily practice.

The experience supports multiple guidance paths without assuming that one worldview fits everyone:

- Scientific wellness
- Mindfulness and reflection
- Spiritual reflection
- Religious practice selected by the user
- Motivational growth
- Mixed guidance

The product never infers religion, diagnoses mental-health conditions, or treats a symbolic reading as medical advice. Every sensitive preference is optional, reviewable, editable, and deletable.

## Core promise

> **Choose what matters to you. Receive a daily ritual that meets you there.**

## Page hierarchy

```text
Public
├── Landing /
├── Sign in /login                         [future integration]
└── Create account /signup                  [future integration]

Setup
└── Template onboarding /onboarding          [wireframe only]
    ├── Welcome and privacy choice
    ├── Goals
    ├── Guidance style
    ├── Current state
    ├── Time and delivery
    └── Review profile

Authenticated product
├── Daily ritual /ritual-dashboard            [wireframe only]
├── Reading center /app/read                  [future integration]
├── Ritual history /app/history               [future integration]
├── Quests and progress /app/quests           [future integration]
├── Rewards /app/rewards                      [future integration]
└── Profile and preferences /app/profile      [future integration]
```

## User journey: selections to daily ritual

```text
Choose a goal
    ↓
Choose a guidance path
    ↓
Choose current state (optional)
    ↓
Choose time, language, and delivery window
    ↓
Review the generated profile
    ↓
Confirm daily ritual plan
    ↓
Receive one small ritual
    ↓
Complete, skip, save, or adjust
    ↓
Profile and recommendations become more relevant over time
```

### Onboarding principles

- One decision per screen or visual group.
- Use cards, chips, icons, and segmented choices instead of required free text.
- Include **Skip**, **Prefer not to say**, and **Change later** wherever appropriate.
- Show a progress marker such as `2 of 6`.
- Explain why a selection helps without implying diagnosis.
- Keep a review screen before any profile is saved.
- Never automatically infer religion, ethnicity, age, or psychological state.

## Onboarding template model

### Step 1: Welcome and boundaries

**User-visible components:**

- Headline: “Build a ritual that feels like yours.”
- Short explanation: select a few preferences; change them anytime.
- Privacy note: “Your choices shape recommendations. You stay in control.”
- Primary action: Continue.
- Secondary action: Skip setup and explore sample ritual.

### Step 2: What would you like more of?

Multi-select cards:

- Calm and stress relief
- Consistency and discipline
- Confidence and self-trust
- Relationships and connection
- Career and direction
- Spiritual reflection
- Physical wellness
- Creative energy

At least one choice is recommended, but the user can skip.

### Step 3: What kind of guidance feels right?

Single or multi-select cards:

- Scientific wellness
- Mindfulness
- Spiritual reflection
- Religious practice
- Motivational coaching
- A blend of approaches

The selected path controls content eligibility. It does not make medical, religious, or psychological claims.

### Step 4: Where are you starting from?

Optional mood/state cards:

- Mentally busy
- Low energy
- Curious
- Restless
- Hopeful
- Focused
- Prefer not to say

This is a current-state preference, not a diagnosis.

### Step 5: Fit the ritual to real life

Choice controls:

- Daily time: 2, 5, or 10 minutes.
- Preferred window: Morning, afternoon, evening, flexible.
- Delivery: Telegram, web, or both after integrations exist.
- Language: English, Urdu, and future supported languages.
- Notification frequency: Daily, weekdays, or manually open.

### Step 6: Review and confirm

Profile summary card:

```text
Your ritual profile
Goal             Calm and stress relief
Guidance         Scientific wellness + Mindfulness
Starting point   Mentally busy
Time             5 minutes
Window           Morning
Language         Urdu
```

Actions:

- Confirm my ritual
- Edit selections
- Skip a category
- Delete this setup

## Daily ritual dashboard wireframe

### Desktop wireframe

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ✦ Fortunis8             DAILY RITUAL · SAMPLE DATA       Maya  ◇ 240 │
├───────────────┬──────────────────────────────────────────────────────┤
│ YOUR PATH     │ Good morning, Maya                                  │
│               │ Your 5-minute ritual is ready.                      │
│ Today         │                                                      │
│ Rituals       │ ┌──────────────────────────────┐ ┌─────────────────┐ │
│ History       │ │ TODAY'S RITUAL               │ │ YOUR PATH       │ │
│ Progress      │ │ 01  Settle the signal       │ │ Calm + Mindful  │ │
│ Profile       │ │                              │ │ Morning · 5 min │ │
│               │ │ 4–4 breathing · 2 minutes   │ │ 7 day streak    │ │
│               │ │ [Begin ritual]              │ │ Edit choices ↗  │ │
│               │ └──────────────────────────────┘ └─────────────────┘ │
│               │                                                      │
│               │ CHOOSE YOUR NEXT SMALL STEP                         │
│               │ ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│               │ │ Breath     │ │ Reflection │ │ Pressure   │         │
│               │ │ 2 min       │ │ 1 prompt   │ │ point      │         │
│               │ │ Start ↗     │ │ Open ↗     │ │ Learn ↗    │         │
│               │ └────────────┘ └────────────┘ └────────────┘         │
│               │                                                      │
│               │ YOUR MOMENTUM                         RECENT RITUALS │
│               │ 7 day streak · 240 diamonds            Today ✓       │
│               │ 3 of 5 rituals this week              Yesterday ✓    │
└───────────────┴──────────────────────────────────────────────────────┘
```

### Mobile wireframe

```text
┌────────────────────────────┐
│ ✦ Fortunis8       ◇ 240    │
│                            │
│ Good morning, Maya.        │
│ Your ritual is ready.      │
│                            │
│ ┌────────────────────────┐ │
│ │ TODAY'S RITUAL         │ │
│ │ Settle the signal      │ │
│ │ 4–4 breathing · 2 min  │ │
│ │ [ Begin ritual ]       │ │
│ └────────────────────────┘ │
│                            │
│ YOUR PATH                 │
│ Calm · Mindfulness        │
│ Morning · 5 minutes       │
│ [Edit choices]            │
│                            │
│ CHOOSE YOUR NEXT STEP     │
│ [Breath] [Reflect]        │
│ [Pressure point]          │
│                            │
│ ✦ 7 day streak            │
│ 3 of 5 rituals this week │
│                            │
│ Today  Rituals  Progress  │
└────────────────────────────┘
```

## Daily ritual content model

A ritual is a structured content item, not an unconstrained AI response:

```text
Ritual
├── type: breath | reflection | movement | pressure_point | reading
├── title
├── duration_seconds
├── guidance_mode: scientific | mindfulness | spiritual | religious | mixed
├── goal_tags
├── age_safety_band
├── language
├── content_version
├── source/review status
└── optional personalization tokens
```

The recommendation engine selects from approved content using the profile. AI may adapt tone or sequencing only within approved content and safety rules. Scientific or religious content should have an appropriate review/source workflow before production use.

## Data model boundary

### Profile preferences

```text
profile_preferences
├── user_id / auth_user_id
├── goals[]
├── guidance_modes[]
├── current_state
├── language
├── daily_duration
├── delivery_window
├── notification_frequency
├── consent_flags
└── updated_at
```

### Ritual activity

```text
ritual_assignments
├── user_id
├── ritual_id
├── assigned_for
├── status: ready | started | completed | skipped
├── completed_at
└── content_version
```

### Safety and privacy requirements

- Do not store sensitive selections unless the user chooses to save them.
- Use `auth_user_id` as ownership authority; never trust client-supplied user IDs.
- Support export, deletion, and preference reset before production launch.
- Include `Prefer not to say` for sensitive categories.
- Do not infer religion, ethnicity, or mental-health status.
- Age should use broad bands unless exact age is genuinely needed.
- Apply stricter safeguards for minors.
- Provide notification opt-out and timezone handling.
- Avoid medical claims for breathing, pressure-point, or wellbeing content.
- Present religious guidance only when selected by the user and sourced through an approved content path.

## Existing backend capabilities

Existing or partially existing capabilities include Telegram onboarding, persona/mood normalization, fortune/tarot/horoscope generation helpers, quests, diamonds, levels, streak logic, Supabase client lifecycle, and FastAPI health/readiness.

These capabilities do **not** yet provide the new product end to end. In particular, the current repository has no verified browser authentication, template onboarding API, profile-preference persistence for this model, ritual catalog, recommendation service, notification scheduler, or daily ritual HTTP API.

## New work required before integration

1. Design and migrate the preference, ritual catalog, assignment, activity, consent, and notification tables.
2. Establish Supabase Auth ownership and row-level security.
3. Build template metadata and versioning so copy changes do not corrupt profiles.
4. Create a reviewed content catalog for scientific, mindfulness, spiritual, and religious paths.
5. Implement recommendation rules before adding unconstrained AI adaptation.
6. Add timezone-aware notification scheduling, opt-out, retries, and delivery logs.
7. Add authenticated FastAPI endpoints for profile review/update and ritual assignment/activity.
8. Add web and Telegram clients only after the API contract is stable.
9. Test mixed guidance, skipped fields, preference edits, duplicate completion, and deleted profiles.

## Visual system for the wireframes

Retain midnight navy, restrained gold, warm parchment, indigo cards, and soft mint completion states. Onboarding should feel lighter and more reassuring than the dashboard: fewer cards per step, generous whitespace, visible progress, and one primary decision. The dashboard should feel like a calm daily desk: one featured ritual, one clear path summary, three optional next steps, and visible momentum without gamification dominating the ritual.

## Current checkpoint boundary

The onboarding and daily ritual dashboard described here are visual wireframes with sample data only. They must not be presented as authenticated, persisted, scientifically validated, religiously authoritative, scheduled, or AI-personalized until the relevant APIs, content review, tests, and safety controls exist.
