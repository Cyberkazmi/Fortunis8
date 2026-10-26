-- Fortunis8 ritual platform migration (additive). Tested on Fortunis8-dev first.
-- No inner BEGIN/COMMIT: the runner wraps it in one transaction.


CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Identity bridge and cached dashboard fields.
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS auth_user_id UUID UNIQUE,
  ADD COLUMN IF NOT EXISTS language TEXT NOT NULL DEFAULT 'en',
  ADD COLUMN IF NOT EXISTS timezone TEXT NOT NULL DEFAULT 'UTC',
  ADD COLUMN IF NOT EXISTS onboarding_status TEXT NOT NULL DEFAULT 'not_started'
    CHECK (onboarding_status IN ('not_started', 'in_progress', 'confirmed', 'skipped')),
  ADD COLUMN IF NOT EXISTS profile_version INTEGER NOT NULL DEFAULT 1;

-- Telegram-first migration compatibility: do not make telegram_id nullable until
-- all existing Telegram flows support a web-only profile.

CREATE TABLE IF NOT EXISTS profile_preferences (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  current_state_key TEXT,
  daily_duration_minutes INTEGER NOT NULL DEFAULT 5
    CHECK (daily_duration_minutes IN (2, 5, 10)),
  preferred_delivery_window TEXT NOT NULL DEFAULT 'morning'
    CHECK (preferred_delivery_window IN ('morning', 'afternoon', 'evening', 'flexible')),
  notification_frequency TEXT NOT NULL DEFAULT 'daily'
    CHECK (notification_frequency IN ('daily', 'weekdays', 'manual')),
  notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  quiet_hours_start TIME,
  quiet_hours_end TIME,
  use_readings BOOLEAN NOT NULL DEFAULT TRUE,
  sensitive_preferences_consent BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS goal_catalog (
  key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS guidance_mode_catalog (
  key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  description TEXT,
  requires_explicit_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS belief_tradition_catalog (
  key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  description TEXT,
  requires_explicit_opt_in BOOLEAN NOT NULL DEFAULT TRUE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS current_state_catalog (
  key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS profile_goals (
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  goal_key TEXT NOT NULL REFERENCES goal_catalog(key),
  priority INTEGER NOT NULL DEFAULT 1 CHECK (priority >= 1),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, goal_key)
);

CREATE TABLE IF NOT EXISTS profile_guidance_modes (
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  guidance_mode_key TEXT NOT NULL REFERENCES guidance_mode_catalog(key),
  priority INTEGER NOT NULL DEFAULT 1 CHECK (priority >= 1),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, guidance_mode_key)
);

CREATE TABLE IF NOT EXISTS profile_belief_preferences (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  tradition_key TEXT REFERENCES belief_tradition_catalog(key),
  interpretation_style TEXT NOT NULL DEFAULT 'reflective'
    CHECK (interpretation_style IN ('reflective', 'serious', 'curious', 'practical')),
  explicitly_selected BOOLEAN NOT NULL DEFAULT FALSE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Versioned, reviewed ritual catalog.
CREATE TABLE IF NOT EXISTS ritual_catalog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stable_key TEXT NOT NULL,
  ritual_type TEXT NOT NULL
    CHECK (ritual_type IN ('breath', 'reflection', 'movement', 'pressure_point', 'visualization', 'reading', 'practical_action')),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  guidance_mode_key TEXT NOT NULL REFERENCES guidance_mode_catalog(key),
  duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
  age_safety_band TEXT NOT NULL DEFAULT 'general',
  source_review_status TEXT NOT NULL DEFAULT 'draft'
    CHECK (source_review_status IN ('draft', 'reviewed', 'published', 'retired')),
  content_version INTEGER NOT NULL DEFAULT 1,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (stable_key, content_version)
);

CREATE TABLE IF NOT EXISTS ritual_tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ritual_id UUID NOT NULL REFERENCES ritual_catalog(id) ON DELETE CASCADE,
  goal_key TEXT REFERENCES goal_catalog(key),
  current_state_key TEXT REFERENCES current_state_catalog(key),
  weight NUMERIC(8, 3) NOT NULL DEFAULT 1.0 CHECK (weight >= 0),
  CHECK (goal_key IS NOT NULL OR current_state_key IS NOT NULL),
  UNIQUE (ritual_id, goal_key, current_state_key)
);

CREATE TABLE IF NOT EXISTS ritual_localizations (
  ritual_id UUID NOT NULL REFERENCES ritual_catalog(id) ON DELETE CASCADE,
  language TEXT NOT NULL,
  title TEXT NOT NULL,
  instructions TEXT NOT NULL,
  safety_note TEXT,
  PRIMARY KEY (ritual_id, language)
);

CREATE TABLE IF NOT EXISTS ritual_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  ritual_id UUID NOT NULL REFERENCES ritual_catalog(id),
  ritual_content_version INTEGER NOT NULL,
  assigned_for_local_date DATE NOT NULL,
  scheduled_at TIMESTAMPTZ,
  slot_key TEXT NOT NULL DEFAULT 'daily_primary',
  status TEXT NOT NULL DEFAULT 'ready'
    CHECK (status IN ('ready', 'started', 'completed', 'skipped', 'expired')),
  source TEXT NOT NULL DEFAULT 'recommendation'
    CHECK (source IN ('recommendation', 'quest', 'manual')),
  idempotency_key TEXT NOT NULL UNIQUE,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, assigned_for_local_date, slot_key)
);

CREATE TABLE IF NOT EXISTS ritual_activity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id UUID NOT NULL REFERENCES ritual_assignments(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN ('viewed', 'started', 'completed', 'skipped')),
  duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Progression and unlocks.
CREATE TABLE IF NOT EXISTS level_definitions (
  level_number INTEGER PRIMARY KEY CHECK (level_number >= 1),
  xp_required INTEGER NOT NULL CHECK (xp_required >= 0),
  title TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS quest_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stable_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  goal_key TEXT REFERENCES goal_catalog(key),
  required_level INTEGER NOT NULL DEFAULT 1 REFERENCES level_definitions(level_number),
  required_guidance_mode_key TEXT REFERENCES guidance_mode_catalog(key),
  completion_rule JSONB NOT NULL,
  xp_reward INTEGER NOT NULL DEFAULT 0 CHECK (xp_reward >= 0),
  diamond_reward INTEGER NOT NULL DEFAULT 0 CHECK (diamond_reward >= 0),
  unlock_key TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_quest_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  quest_definition_id UUID NOT NULL REFERENCES quest_definitions(id),
  assignment_id UUID REFERENCES ritual_assignments(id),
  period_key TEXT NOT NULL,
  progress_value INTEGER NOT NULL DEFAULT 0 CHECK (progress_value >= 0),
  target_value INTEGER NOT NULL DEFAULT 1 CHECK (target_value > 0),
  status TEXT NOT NULL DEFAULT 'available'
    CHECK (status IN ('available', 'active', 'completed', 'expired')),
  completion_idempotency_key TEXT UNIQUE,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, quest_definition_id, period_key)
);

CREATE TABLE IF NOT EXISTS xp_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL CHECK (source_type IN ('ritual', 'quest', 'streak', 'bonus')),
  source_id UUID,
  amount INTEGER NOT NULL CHECK (amount > 0),
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS diamond_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL CHECK (source_type IN ('ritual', 'quest', 'streak', 'reading', 'bonus')),
  source_id UUID,
  amount INTEGER NOT NULL CHECK (amount > 0),
  reason TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_unlocks (
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  unlock_key TEXT NOT NULL,
  source_level INTEGER REFERENCES level_definitions(level_number),
  unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, unlock_key)
);

-- 4. Channel preferences and delivery audit.
CREATE TABLE IF NOT EXISTS notification_preferences (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  timezone TEXT NOT NULL DEFAULT 'UTC',
  channels TEXT[] NOT NULL DEFAULT ARRAY['telegram'],
  preferred_window TEXT NOT NULL DEFAULT 'morning'
    CHECK (preferred_window IN ('morning', 'afternoon', 'evening', 'flexible')),
  frequency TEXT NOT NULL DEFAULT 'daily'
    CHECK (frequency IN ('daily', 'weekdays', 'manual')),
  quiet_hours_start TIME,
  quiet_hours_end TIME,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  opted_in_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  assignment_id UUID REFERENCES ritual_assignments(id) ON DELETE SET NULL,
  channel TEXT NOT NULL CHECK (channel IN ('web', 'telegram', 'app')),
  scheduled_for TIMESTAMPTZ NOT NULL,
  sent_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'sent', 'failed', 'skipped', 'cancelled')),
  provider_message_id TEXT,
  failure_code TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Indexes for user dashboards, scheduler queries, and ledgers.
CREATE INDEX IF NOT EXISTS idx_profiles_auth_user_id ON profiles(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_profile_goals_user_id ON profile_goals(user_id) WHERE active;
CREATE INDEX IF NOT EXISTS idx_profile_guidance_modes_user_id ON profile_guidance_modes(user_id) WHERE active;
CREATE INDEX IF NOT EXISTS idx_ritual_assignments_user_date ON ritual_assignments(user_id, assigned_for_local_date DESC);
CREATE INDEX IF NOT EXISTS idx_ritual_assignments_scheduler ON ritual_assignments(scheduled_at, status);
CREATE INDEX IF NOT EXISTS idx_ritual_activity_user_created ON ritual_activity(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_quest_progress_user_status ON user_quest_progress(user_id, status);
CREATE INDEX IF NOT EXISTS idx_xp_ledger_user_created ON xp_ledger(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_diamond_ledger_user_created ON diamond_ledger(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_scheduler ON notification_deliveries(scheduled_for, status);
CREATE INDEX IF NOT EXISTS idx_notification_user_created ON notification_deliveries(user_id, created_at DESC);

-- Apply the existing timestamp trigger to new mutable preference rows if the
-- function already exists in the MVP schema.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at') THEN
    EXECUTE 'CREATE TRIGGER trg_profile_preferences_updated_at
      BEFORE UPDATE ON profile_preferences
      FOR EACH ROW EXECUTE FUNCTION set_updated_at()';
    EXECUTE 'CREATE TRIGGER trg_profile_belief_preferences_updated_at
      BEFORE UPDATE ON profile_belief_preferences
      FOR EACH ROW EXECUTE FUNCTION set_updated_at()';
    EXECUTE 'CREATE TRIGGER trg_notification_preferences_updated_at
      BEFORE UPDATE ON notification_preferences
      FOR EACH ROW EXECUTE FUNCTION set_updated_at()';
  END IF;
EXCEPTION WHEN duplicate_object THEN
  NULL;
END $$;


-- 2. Row Level Security. Backend uses the service role (bypasses RLS).
CREATE OR REPLACE FUNCTION public.current_profile_id() RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT id FROM public.profiles WHERE auth_user_id = auth.uid() $$;
REVOKE ALL ON FUNCTION public.current_profile_id() FROM public;
GRANT EXECUTE ON FUNCTION public.current_profile_id() TO authenticated;
CREATE POLICY profile_owner_select ON public.profiles FOR SELECT TO authenticated USING (auth_user_id = auth.uid());
ALTER TABLE public.goal_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY goal_catalog_public_read ON public.goal_catalog FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.guidance_mode_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY guidance_mode_catalog_public_read ON public.guidance_mode_catalog FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.belief_tradition_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY belief_tradition_catalog_public_read ON public.belief_tradition_catalog FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.current_state_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY current_state_catalog_public_read ON public.current_state_catalog FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.ritual_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY ritual_catalog_public_read ON public.ritual_catalog FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.ritual_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY ritual_tags_public_read ON public.ritual_tags FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.ritual_localizations ENABLE ROW LEVEL SECURITY;
CREATE POLICY ritual_localizations_public_read ON public.ritual_localizations FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.level_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY level_definitions_public_read ON public.level_definitions FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.quest_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY quest_definitions_public_read ON public.quest_definitions FOR SELECT TO anon, authenticated USING (true);
ALTER TABLE public.profile_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY profile_preferences_owner_select ON public.profile_preferences FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
CREATE POLICY profile_preferences_owner_insert ON public.profile_preferences FOR INSERT TO authenticated WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY profile_preferences_owner_update ON public.profile_preferences FOR UPDATE TO authenticated USING (user_id = public.current_profile_id()) WITH CHECK (user_id = public.current_profile_id());
ALTER TABLE public.profile_goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY profile_goals_owner_select ON public.profile_goals FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
CREATE POLICY profile_goals_owner_insert ON public.profile_goals FOR INSERT TO authenticated WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY profile_goals_owner_update ON public.profile_goals FOR UPDATE TO authenticated USING (user_id = public.current_profile_id()) WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY profile_goals_owner_delete ON public.profile_goals FOR DELETE TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.profile_guidance_modes ENABLE ROW LEVEL SECURITY;
CREATE POLICY profile_guidance_modes_owner_select ON public.profile_guidance_modes FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
CREATE POLICY profile_guidance_modes_owner_insert ON public.profile_guidance_modes FOR INSERT TO authenticated WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY profile_guidance_modes_owner_update ON public.profile_guidance_modes FOR UPDATE TO authenticated USING (user_id = public.current_profile_id()) WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY profile_guidance_modes_owner_delete ON public.profile_guidance_modes FOR DELETE TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.profile_belief_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY profile_belief_preferences_owner_select ON public.profile_belief_preferences FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
CREATE POLICY profile_belief_preferences_owner_insert ON public.profile_belief_preferences FOR INSERT TO authenticated WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY profile_belief_preferences_owner_update ON public.profile_belief_preferences FOR UPDATE TO authenticated USING (user_id = public.current_profile_id()) WITH CHECK (user_id = public.current_profile_id());
ALTER TABLE public.ritual_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY ritual_assignments_owner_select ON public.ritual_assignments FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.ritual_activity ENABLE ROW LEVEL SECURITY;
CREATE POLICY ritual_activity_owner_select ON public.ritual_activity FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.user_quest_progress ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_quest_progress_owner_select ON public.user_quest_progress FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.xp_ledger ENABLE ROW LEVEL SECURITY;
CREATE POLICY xp_ledger_owner_select ON public.xp_ledger FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.diamond_ledger ENABLE ROW LEVEL SECURITY;
CREATE POLICY diamond_ledger_owner_select ON public.diamond_ledger FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.user_unlocks ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_unlocks_owner_select ON public.user_unlocks FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY notification_preferences_owner_select ON public.notification_preferences FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
CREATE POLICY notification_preferences_owner_insert ON public.notification_preferences FOR INSERT TO authenticated WITH CHECK (user_id = public.current_profile_id());
CREATE POLICY notification_preferences_owner_update ON public.notification_preferences FOR UPDATE TO authenticated USING (user_id = public.current_profile_id()) WITH CHECK (user_id = public.current_profile_id());
ALTER TABLE public.notification_deliveries ENABLE ROW LEVEL SECURITY;
CREATE POLICY notification_deliveries_owner_select ON public.notification_deliveries FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
