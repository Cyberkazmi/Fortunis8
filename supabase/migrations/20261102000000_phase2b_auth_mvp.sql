-- Fortunis8 Phase 2B authenticated MVP foundation.
-- Artifact only: do not execute against live Supabase without owner approval.
-- Depends on 20261025000000_ritual_platform.sql and 20261026000000_subscriptions.sql.

-- Web-only accounts must be able to own a profile without a Telegram identity.
ALTER TABLE public.profiles
  ALTER COLUMN telegram_id DROP NOT NULL;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS profile_owner_select ON public.profiles;
DROP POLICY IF EXISTS profile_owner_insert ON public.profiles;
DROP POLICY IF EXISTS profile_owner_update ON public.profiles;
CREATE POLICY profile_owner_select ON public.profiles
  FOR SELECT TO authenticated USING (auth.uid() = auth_user_id);
CREATE POLICY profile_owner_insert ON public.profiles
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = auth_user_id);
CREATE POLICY profile_owner_update ON public.profiles
  FOR UPDATE TO authenticated
  USING (auth.uid() = auth_user_id)
  WITH CHECK (auth.uid() = auth_user_id);

-- Legacy user-owned records use the trusted profile identity bridge.
DO $$
DECLARE
  table_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY['fortune_readings', 'rewards', 'quests', 'daily_streaks', 'mini_games'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I_owner_select ON public.%I', table_name, table_name);
    EXECUTE format(
      'CREATE POLICY %I_owner_select ON public.%I FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM public.profiles p WHERE p.id = user_id AND p.auth_user_id = auth.uid()))',
      table_name, table_name
    );
  END LOOP;
END $$;

-- Ensure the normalized web profile tables retain owner-only access after the
-- existing additive migration has been applied.
ALTER TABLE public.profile_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_guidance_modes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_belief_preferences ENABLE ROW LEVEL SECURITY;

-- The backend uses the server-only service role for normalized writes. Browser
-- clients receive only their own rows through authenticated SELECT policies.
