-- Fortunis8 premium/subscriptions (additive). Tested on Fortunis8-dev first.
CREATE TABLE IF NOT EXISTS plans (
  key TEXT PRIMARY KEY,
  name_en TEXT NOT NULL,
  name_ur TEXT NOT NULL,
  billing_interval TEXT CHECK (billing_interval IN ('month','year')),
  price_pkr INTEGER CHECK (price_pkr >= 0),
  price_usd_cents INTEGER CHECK (price_usd_cents >= 0),
  trial_days INTEGER NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS plan_features (
  plan_key TEXT NOT NULL REFERENCES plans(key) ON DELETE CASCADE,
  feature_key TEXT NOT NULL,
  limit_value INTEGER,
  PRIMARY KEY (plan_key, feature_key)
);
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  plan_key TEXT NOT NULL REFERENCES plans(key),
  status TEXT NOT NULL CHECK (status IN ('trialing','active','past_due','cancelled','expired')),
  provider TEXT NOT NULL CHECK (provider IN ('telegram_stars','jazzcash','easypaisa','card','manual')),
  provider_ref TEXT,
  current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (provider, provider_ref)
);
CREATE TABLE IF NOT EXISTS payment_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
  provider TEXT NOT NULL,
  event_type TEXT NOT NULL,
  amount_minor INTEGER,
  currency TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status, current_period_end DESC);

CREATE OR REPLACE VIEW user_entitlements WITH (security_invoker = true) AS
SELECT p.id AS user_id,
  COALESCE((SELECT s.plan_key FROM subscriptions s WHERE s.user_id = p.id
    AND s.status IN ('trialing','active') AND s.current_period_end > NOW()
    ORDER BY s.current_period_end DESC LIMIT 1), 'free') AS plan_key
FROM profiles p;

INSERT INTO plans(key,name_en,name_ur,billing_interval,price_pkr,price_usd_cents,trial_days) VALUES
 ('free','Free','مفت',NULL,0,0,0),
 ('premium_monthly','Premium Monthly','پریمیم ماہانہ','month',499,499,7),
 ('premium_yearly','Premium Yearly','پریمیم سالانہ','year',3999,3999,7)
ON CONFLICT (key) DO NOTHING;
INSERT INTO plan_features(plan_key,feature_key,limit_value) VALUES
 ('free','daily_rituals',1),('free','max_goals',2),('free','max_guidance_modes',1),('free','daily_readings',1),('free','history_days',7),
 ('premium_monthly','daily_rituals',NULL),('premium_monthly','max_goals',13),('premium_monthly','max_guidance_modes',NULL),('premium_monthly','deep_rituals',NULL),('premium_monthly','ai_reflection',NULL),('premium_monthly','deep_readings',NULL),('premium_monthly','history_days',NULL),('premium_monthly','streak_freezes_per_month',2),('premium_monthly','custom_reminders',NULL),('premium_monthly','premium_quests',NULL),
 ('premium_yearly','daily_rituals',NULL),('premium_yearly','max_goals',13),('premium_yearly','max_guidance_modes',NULL),('premium_yearly','deep_rituals',NULL),('premium_yearly','ai_reflection',NULL),('premium_yearly','deep_readings',NULL),('premium_yearly','history_days',NULL),('premium_yearly','streak_freezes_per_month',2),('premium_yearly','custom_reminders',NULL),('premium_yearly','premium_quests',NULL)
ON CONFLICT DO NOTHING;

ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY plans_public_read ON plans FOR SELECT TO anon, authenticated USING (is_active);
CREATE POLICY plan_features_public_read ON plan_features FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY subscriptions_owner_select ON subscriptions FOR SELECT TO authenticated USING (user_id = public.current_profile_id());
-- payment_events: service role only (no policies).
