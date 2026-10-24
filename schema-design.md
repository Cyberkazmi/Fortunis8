# Fortunis8 Profile and Custom Ritual Schema Design

## Scope

This is a design specification for the Telegram-first, web-SaaS Fortunis8 platform. It supports multiple user belief/guidance systems, goal-based ritual paths, automated notifications, quests, XP, levels, unlocks, streaks, and optional readings.

This document is a **draft design only**. It has not been applied to Supabase, production, the existing Fortunis8 repository, or any live user data.

## Design principles

1. **One identity, many channels.** A user may start in Telegram, continue on the web, and later use a mobile app. `auth_user_id` is the authoritative browser/app identity; `telegram_id` is a linked channel identifier.
2. **Selections, not diagnosis.** Profiles store user-selected preferences and optional current-state tags. They do not store an inferred psychological diagnosis.
3. **Belief-flexible, user-controlled content.** A user can choose scientific wellness, mindfulness, spiritual reflection, religious practice, motivational guidance, or a mix. The system never infers religion or belief.
4. **Catalog first, AI second.** Rituals are approved catalog items with tags, safety notes, language, and versioning. AI may personalize wording or sequencing only after eligibility filtering.
5. **Server-authoritative progression.** XP, diamonds, levels, unlocks, quest completion, and daily rewards are recorded in server-side ledgers with idempotency keys.
6. **Timezone-aware automation.** Notification preferences belong to the user profile and deliveries are logged independently from the ritual assignment.
7. **Privacy by default.** Sensitive choices are optional, reviewable, editable, and deletable. Row ownership is enforced by `auth_user_id` and database policies.

## Existing schema compatibility

The current MVP schema contains `profiles`, `fortune_readings`, `rewards`, `quests`, `daily_streaks`, and `mini_games`. The draft keeps those concepts compatible while adding normalized preference, ritual, progression, and notification tables.

Recommended compatibility changes:

- Keep `profiles.id` as the internal primary key.
- Add nullable unique `profiles.auth_user_id` for Supabase Auth users.
- Keep `profiles.telegram_id` during migration; make it nullable only after all existing Telegram flows support a profile without Telegram.
- Keep legacy `diamonds`, `streak_count`, and `level` as cached read models while ledgers become the source of truth.
- Add `timezone` and `language` to support scheduled, localized delivery.
- Avoid putting arrays or arbitrary client JSON in the profile when a normalized relationship is needed for filtering and RLS.

## Canonical profile structure

```text
profiles
├── id: internal UUID
├── auth_user_id: Supabase Auth UUID, nullable during Telegram-first migration
├── telegram_id: linked Telegram identifier, nullable after migration
├── display_name / Telegram identity fields
├── language
├── timezone
├── zodiac_sign and optional birth metadata
├── selected_persona and current_mood (legacy-compatible fields)
├── diamonds / streak_count / level (cached summary fields)
├── onboarding_status
├── profile_version
└── timestamps

profile_preferences
├── user_id
├── current_state_key (optional self-selected state, not diagnosis)
├── daily_duration_minutes
├── preferred_delivery_window
├── notification_frequency
├── notifications_enabled
├── quiet_hours
├── consent flags
└── timestamps

profile_goals
├── user_id
├── goal_key
├── priority
└── active

profile_guidance_modes
├── user_id
├── guidance_mode_key
├── priority
└── active

profile_belief_preferences
├── user_id
├── tradition_key (optional catalog key, user-selected only)
├── interpretation_style
├── use_readings
└── active
```

### Example structured profile

```json
{
  "user_id": "auth-user-uuid",
  "language": "ur",
  "timezone": "Asia/Karachi",
  "goals": ["career_confidence", "consistent_action"],
  "guidance_modes": ["practical_action", "mindfulness"],
  "current_state": "curious",
  "daily_duration_minutes": 5,
  "preferred_delivery_window": "morning",
  "notification_frequency": "daily",
  "use_readings": false,
  "onboarding_status": "confirmed"
}
```

## Controlled vocabularies

Catalog keys should be stable machine values with localized display copy stored separately or versioned in the catalog.

### Goals

Examples: `calm`, `confidence`, `career_confidence`, `business_growth`, `financial_discipline`, `study_focus`, `exam_preparation`, `relationships`, `creative_energy`, `sleep_recovery`, `physical_wellness`, `spiritual_reflection`, `consistency`.

### Guidance modes

Examples: `scientific_wellness`, `mindfulness`, `practical_action`, `motivational`, `spiritual_reflection`, `religious_practice`, `visualization`, `mixed`.

A mode describes the requested framing, not a claim that all content in that mode is scientifically or religiously authoritative.

### Belief traditions

If the product eventually offers tradition-specific content, use an explicit `belief_tradition_catalog` and require opt-in. A user may leave this empty. The system must never infer a tradition from language, location, name, zodiac sign, or reading behavior.

### Current state

Examples: `mentally_busy`, `low_energy`, `curious`, `restless`, `hopeful`, `focused`, `prefer_not_to_say`.

These are self-selected context tags only. The UI and AI must not label them as mental-health diagnoses.

## Ritual catalog and recommendation model

```text
ritual_catalog
├── id / stable key
├── ritual_type: breath | reflection | movement | pressure_point | visualization | reading | practical_action
├── title and description
├── guidance_mode
├── source/review status
├── age_safety_band
├── duration_seconds
├── content_version
├── active/published flags
└── timestamps

ritual_tags
├── ritual_id
├── goal_key (optional)
├── current_state_key (optional)
├── audience_key (optional)
└── weight
```

At least one of `goal_key` or `current_state_key` is required for a tag row; either may be used alone so a ritual can match a goal, a self-selected current state, or both.
ritual_localizations
├── ritual_id
├── language
├── title
├── instructions
├── safety_note
└── content_version
```

Recommendation flow:

```text
profile selections
  → eligibility filter
  → guidance-mode and goal match
  → duration/language/time filter
  → level/unlock filter
  → cooldown and recent-history filter
  → deterministic selection or reviewed AI wording
  → assignment
```

A ritual assignment stores the exact catalog version delivered to the user so future catalog edits do not rewrite history.

## Daily ritual and activity tables

```text
ritual_assignments
├── user_id
├── ritual_id
├── ritual_content_version
├── assigned_for_local_date
├── scheduled_at
├── status: ready | started | completed | skipped | expired
├── source: recommendation | quest | manual
├── idempotency_key
└── timestamps

ritual_activity
├── assignment_id
├── user_id
├── event_type: viewed | started | completed | skipped
├── duration_seconds
├── metadata limited to approved fields
└── created_at
```

Unique constraint: one assignment per user, local date, and ritual slot unless an explicit multi-ritual plan allows more.

## Game progression

```text
level_definitions
├── level_number
├── xp_required
├── title
└── active

quest_definitions
├── key
├── title/description
├── goal_key
├── required_level
├── required_guidance_mode (optional)
├── completion_rule JSON/schema version
├── xp_reward
├── diamond_reward
├── unlock_key (optional)
└── active

user_quest_progress
├── user_id
├── quest_definition_id
├── assignment_id (optional)
├── period_key
├── progress_value
├── target_value
├── status: available | active | completed | expired
├── completion_idempotency_key
└── timestamps

xp_ledger
├── user_id
├── source_type: ritual | quest | streak | bonus
├── source_id
├── amount
├── idempotency_key UNIQUE
└── created_at

diamond_ledger
├── user_id
├── source_type
├── source_id
├── amount
├── reason
├── idempotency_key UNIQUE
└── created_at

user_unlocks
├── user_id
├── unlock_key
├── unlocked_at
└── source_level
```

`profiles.level`, `profiles.diamonds`, and `profiles.streak_count` can remain cached for fast dashboard reads, but every mutation must originate from a transaction that writes the relevant ledger and updates the cached summary.

## Notification scheduling

```text
notification_preferences
├── user_id UNIQUE
├── channels: web | telegram | future_app
├── timezone
├── preferred_window
├── frequency
├── quiet_hours_start/end
├── enabled
├── opted_in_at
└── updated_at

notification_deliveries
├── user_id
├── assignment_id (optional)
├── channel
├── scheduled_for
├── sent_at
├── status: queued | sent | failed | skipped | cancelled
├── provider_message_id
├── failure_code (no secret payload)
├── retry_count
└── idempotency_key UNIQUE
```

The scheduler should calculate local delivery times from the user timezone, respect quiet hours, and create a delivery row before sending. Telegram and future app/web push are delivery adapters over the same assignment and profile source of truth.

## Authentication and ownership

- Supabase Auth creates the authenticated identity.
- `profiles.auth_user_id` maps that identity to one profile.
- Telegram linking is explicit and server-controlled; a client cannot claim another `telegram_id`.
- Every child table includes `user_id` or reaches one through a trusted foreign key.
- RLS policies allow a signed-in user to select/update only rows belonging to their own `auth_user_id`.
- Catalog tables are read-only to normal users; admin/content-review roles manage them separately.
- Scheduler/service-role operations are isolated from browser policies and are audited.

## Migration and rollout order

1. Add nullable `auth_user_id`, `language`, `timezone`, and onboarding status to `profiles`.
2. Create catalog tables and seed only reviewed, non-medical sample content.
3. Create normalized profile preference tables.
4. Create ritual assignment/activity tables.
5. Create level, quest, XP, diamond, and unlock tables.
6. Create notification preference/delivery tables.
7. Add RLS and ownership tests.
8. Backfill existing Telegram users into preferences only from explicit existing fields; do not infer new beliefs or goals.
9. Run dual-write or compatibility adapters for legacy quests/rewards.
10. Switch dashboard reads to the new source of truth after reconciliation checks.

## Explicitly not covered by this draft

- Production migration execution.
- Supabase Auth enablement.
- Notification provider credentials.
- Final religious or scientific content approval.
- AI prompt implementation.
- Mobile app tables beyond channel-ready notification fields.

## Acceptance boundary

This design is ready for architecture review when the team agrees on:

- Profile ownership and Telegram-to-web linking rules.
- Controlled goal/guidance vocabulary.
- Content review process for each guidance mode.
- Level/XP formulas and unlock policy.
- Notification channels, timezone, quiet hours, and opt-out behavior.
- Data retention, export, and deletion rules.
