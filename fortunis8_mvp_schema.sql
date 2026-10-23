BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- Fortunis8 MVP Schema
-- Ordered by dependency: profiles first, then child tables.
-- =====================================================

CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id TEXT UNIQUE NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  zodiac_sign TEXT,
  selected_persona TEXT NOT NULL DEFAULT 'Oracle of Light',
  current_mood TEXT NOT NULL DEFAULT 'balanced',
  diamonds INTEGER NOT NULL DEFAULT 0 CHECK (diamonds >= 0),
  streak_count INTEGER NOT NULL DEFAULT 0 CHECK (streak_count >= 0),
  level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE fortune_readings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  reading_type TEXT NOT NULL CHECK (reading_type IN ('horoscope', 'tarot', 'palm', 'general')),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  question TEXT,
  card_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE rewards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source TEXT NOT NULL CHECK (source IN ('fortune', 'streak', 'quest', 'bonus', 'mini_game')),
  amount INTEGER NOT NULL CHECK (amount >= 0),
  reason TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE quests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'expired')),
  reward_diamonds INTEGER NOT NULL DEFAULT 0 CHECK (reward_diamonds >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE daily_streaks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  streak_date DATE NOT NULL,
  streak_count INTEGER NOT NULL DEFAULT 0 CHECK (streak_count >= 0),
  bonus_diamonds INTEGER NOT NULL DEFAULT 0 CHECK (bonus_diamonds >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, streak_date)
);

CREATE TABLE mini_games (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  game_type TEXT NOT NULL CHECK (game_type IN ('quiz', 'memory', 'fortune_spin', 'card_match')),
  score INTEGER NOT NULL DEFAULT 0 CHECK (score >= 0),
  diamonds_awarded INTEGER NOT NULL DEFAULT 0 CHECK (diamonds_awarded >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX idx_profiles_telegram_id ON profiles(telegram_id);
CREATE INDEX idx_fortune_readings_user_id ON fortune_readings(user_id);
CREATE INDEX idx_fortune_readings_created_at ON fortune_readings(created_at DESC);
CREATE INDEX idx_rewards_user_id ON rewards(user_id);
CREATE INDEX idx_quests_user_id ON quests(user_id);
CREATE INDEX idx_daily_streaks_user_id ON daily_streaks(user_id);
CREATE INDEX idx_mini_games_user_id ON mini_games(user_id);

-- =====================================================
-- Trigger: update profile timestamps automatically
-- =====================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_profiles_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- =====================================================
-- Sample seed data
-- Order matters: profiles first, then dependent records.
-- =====================================================

INSERT INTO profiles (
  id,
  telegram_id,
  username,
  first_name,
  last_name,
  zodiac_sign,
  selected_persona,
  diamonds,
  streak_count,
  level
) VALUES
  (
    '11111111-1111-4111-8111-111111111111',
    '10001',
    'mystic_aisha',
    'Aisha',
    'Rahman',
    'Capricorn',
    'Oracle of Light',
    120,
    5,
    3
  ),
  (
    '22222222-2222-4222-8222-222222222222',
    '10002',
    'zephyr_omar',
    'Omar',
    'Khan',
    'Leo',
    'Sun Warrior',
    85,
    3,
    2
  );

INSERT INTO fortune_readings (
  id,
  user_id,
  reading_type,
  title,
  content,
  question,
  card_name,
  created_at
) VALUES
  (
    '33333333-3333-4333-8333-333333333333',
    '11111111-1111-4111-8111-111111111111',
    'horoscope',
    'Daily Horoscope',
    'This is a powerful day for long-term focus. Your work will deepen when you trust your instincts and resist the urge to chase approval. The path ahead opens through quiet confidence.',
    'What should I focus on today?',
    NULL,
    '2026-10-21 09:00:00+00'
  ),
  (
    '44444444-4444-4444-8444-444444444444',
    '11111111-1111-4111-8111-111111111111',
    'tarot',
    'Tarot Guidance',
    'The Star appears, bringing calm, direction, and hope. You are not lost; you are moving into a brighter phase of clarity. Keep your faith in the next step, even if it is still hidden.',
    'How do I make the next chapter wiser?',
    'The Star',
    '2026-10-21 09:15:00+00'
  ),
  (
    '55555555-5555-4555-8555-555555555555',
    '22222222-2222-4222-8222-222222222222',
    'palm',
    'Palm Reading',
    'Your life line shows resilience and a desire to create your own path. The head line reveals strong thinking and a need to turn ideas into action. The heart line shows loyalty and deep emotional truth.',
    'What do my hands reveal?',
    NULL,
    '2026-10-21 10:00:00+00'
  );

INSERT INTO rewards (
  id,
  user_id,
  source,
  amount,
  reason,
  created_at
) VALUES
  (
    '66666666-6666-4666-8666-666666666666',
    '11111111-1111-4111-8111-111111111111',
    'fortune',
    20,
    'Completed daily horoscope reading',
    '2026-10-21 09:05:00+00'
  ),
  (
    '77777777-7777-4777-8777-777777777777',
    '11111111-1111-4111-8111-111111111111',
    'streak',
    15,
    'Daily streak bonus',
    '2026-10-21 09:20:00+00'
  ),
  (
    '88888888-8888-4888-8888-888888888888',
    '11111111-1111-4111-8111-111111111111',
    'quest',
    30,
    'Completed the Daily Fortune quest',
    '2026-10-21 09:30:00+00'
  ),
  (
    '99999999-9999-4999-8999-999999999999',
    '22222222-2222-4222-8222-222222222222',
    'mini_game',
    40,
    'Won a fortune spin mini-game',
    '2026-10-21 10:10:00+00'
  );

INSERT INTO quests (
  id,
  user_id,
  title,
  description,
  status,
  reward_diamonds,
  created_at,
  completed_at
) VALUES
  (
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    '11111111-1111-4111-8111-111111111111',
    'Daily Fortune',
    'Read your horoscope and complete your daily fortune check-in.',
    'completed',
    25,
    '2026-10-21 09:00:00+00',
    '2026-10-21 09:05:00+00'
  ),
  (
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    '22222222-2222-4222-8222-222222222222',
    'Mystic Streak',
    'Keep a 3-day streak and stay consistent with your fortune ritual.',
    'active',
    35,
    '2026-10-21 10:00:00+00',
    NULL
  );

INSERT INTO daily_streaks (
  id,
  user_id,
  streak_date,
  streak_count,
  bonus_diamonds,
  created_at
) VALUES
  (
    'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    '11111111-1111-4111-8111-111111111111',
    '2026-10-21',
    5,
    15,
    '2026-10-21 09:25:00+00'
  ),
  (
    'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    '22222222-2222-4222-8222-222222222222',
    '2026-10-21',
    3,
    10,
    '2026-10-21 10:05:00+00'
  );

INSERT INTO mini_games (
  id,
  user_id,
  game_type,
  score,
  diamonds_awarded,
  created_at
) VALUES
  (
    'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    '11111111-1111-4111-8111-111111111111',
    'quiz',
    120,
    25,
    '2026-10-21 09:35:00+00'
  ),
  (
    'ffffffff-ffff-4fff-8fff-ffffffffffff',
    '22222222-2222-4222-8222-222222222222',
    'fortune_spin',
    90,
    30,
    '2026-10-21 10:15:00+00'
  );

COMMIT;
