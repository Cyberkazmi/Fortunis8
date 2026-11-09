-- Fortunis8 additive core schema. This migration creates only Fortunis8-owned
-- objects; it does not alter, rename, or drop any existing project table.
begin;

create table if not exists public.fortunis8_accounts (
    telegram_user_id bigint primary key references public.fortunis8_users(telegram_user_id) on delete cascade,
    diamonds integer not null default 0 check (diamonds >= 0),
    level integer not null default 1 check (level >= 1),
    streak_count integer not null default 0 check (streak_count >= 0),
    last_daily_date date,
    selected_persona text not null default 'Wizard',
    premium_reading_credits integer not null default 0 check (premium_reading_credits >= 0),
    created_at timestamptz not null default pg_catalog.now(),
    updated_at timestamptz not null default pg_catalog.now(),
    constraint fortunis8_accounts_persona_check check (selected_persona in (
        'Mario', 'Tarzan', 'Hercules', 'Dragon', 'Ninja', 'Wizard', 'Phoenix',
        'Spartan', 'Viking', 'Samurai', 'Pirate', 'Jedi'
    ))
);

create table if not exists public.fortunis8_events (
    id bigint generated always as identity primary key,
    telegram_user_id bigint not null references public.fortunis8_accounts(telegram_user_id) on delete cascade,
    event_type text not null check (event_type in ('daily_reward', 'game_reward', 'charity_quest', 'star_purchase', 'premium_use')),
    diamond_delta integer not null default 0,
    idempotency_key text not null unique,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default pg_catalog.now()
);

create index if not exists fortunis8_events_user_created_idx
    on public.fortunis8_events (telegram_user_id, created_at desc);

create table if not exists public.fortunis8_readings (
    id uuid primary key default gen_random_uuid(),
    telegram_user_id bigint not null references public.fortunis8_accounts(telegram_user_id) on delete cascade,
    reading_type text not null check (reading_type in ('palm_basic', 'palm_premium', 'tarot', 'horoscope')),
    title text not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default pg_catalog.now()
);

create index if not exists fortunis8_readings_user_created_idx
    on public.fortunis8_readings (telegram_user_id, created_at desc);

create table if not exists public.fortunis8_game_sessions (
    id uuid primary key,
    telegram_user_id bigint not null references public.fortunis8_accounts(telegram_user_id) on delete cascade,
    game_key text not null,
    difficulty text not null check (difficulty in ('easy', 'hard')),
    prompt text not null,
    options jsonb not null,
    correct_answer text not null,
    reward_diamonds integer not null check (reward_diamonds between 0 and 100),
    created_at timestamptz not null default pg_catalog.now(),
    expires_at timestamptz not null,
    completed_at timestamptz,
    was_correct boolean
);

create index if not exists fortunis8_games_user_created_idx
    on public.fortunis8_game_sessions (telegram_user_id, created_at desc);

create table if not exists public.fortunis8_pending_invoices (
    invoice_payload text primary key,
    telegram_user_id bigint not null references public.fortunis8_accounts(telegram_user_id) on delete cascade,
    product text not null check (product = 'premium_palm_reading'),
    focus text not null check (focus in ('general', 'love', 'work', 'growth')),
    amount_stars integer not null check (amount_stars > 0),
    currency text not null default 'XTR' check (currency = 'XTR'),
    created_at timestamptz not null default pg_catalog.now(),
    expires_at timestamptz not null default (pg_catalog.now() + interval '30 minutes')
);

create table if not exists public.fortunis8_star_payments (
    id bigint generated always as identity primary key,
    telegram_payment_charge_id text not null unique,
    invoice_payload text not null unique,
    telegram_user_id bigint not null references public.fortunis8_accounts(telegram_user_id) on delete cascade,
    product text not null check (product = 'premium_palm_reading'),
    focus text not null check (focus in ('general', 'love', 'work', 'growth')),
    total_amount integer not null check (total_amount > 0),
    currency text not null check (currency = 'XTR'),
    created_at timestamptz not null default pg_catalog.now()
);

alter table public.fortunis8_accounts enable row level security;
alter table public.fortunis8_events enable row level security;
alter table public.fortunis8_readings enable row level security;
alter table public.fortunis8_game_sessions enable row level security;
alter table public.fortunis8_pending_invoices enable row level security;
alter table public.fortunis8_star_payments enable row level security;

revoke all on table public.fortunis8_accounts, public.fortunis8_events,
    public.fortunis8_readings, public.fortunis8_game_sessions,
    public.fortunis8_pending_invoices, public.fortunis8_star_payments
    from anon, authenticated;
grant all on table public.fortunis8_accounts, public.fortunis8_events,
    public.fortunis8_readings, public.fortunis8_game_sessions,
    public.fortunis8_pending_invoices, public.fortunis8_star_payments
    to service_role;

create or replace function public.fortunis8_claim_daily(p_telegram_user_id bigint)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_account public.fortunis8_accounts%rowtype;
    v_today date := (pg_catalog.now() at time zone 'UTC')::date;
    v_streak integer;
    v_reward integer;
begin
    insert into public.fortunis8_accounts (telegram_user_id)
    values (p_telegram_user_id) on conflict (telegram_user_id) do nothing;
    select * into v_account from public.fortunis8_accounts
      where telegram_user_id = p_telegram_user_id for update;
    if not found then return pg_catalog.jsonb_build_object('ok', false, 'reason', 'account_missing'); end if;
    if v_account.last_daily_date = v_today then
        return pg_catalog.jsonb_build_object('ok', true, 'claimed', false,
            'diamonds', v_account.diamonds, 'streak', v_account.streak_count, 'reward', 0);
    end if;
    v_streak := case when v_account.last_daily_date = v_today - 1
        then v_account.streak_count + 1 else 1 end;
    v_reward := 2 + least(v_streak - 1, 6);
    update public.fortunis8_accounts set
        diamonds = diamonds + v_reward,
        level = greatest(1, 1 + ((diamonds + v_reward) / 50)),
        streak_count = v_streak,
        last_daily_date = v_today,
        updated_at = pg_catalog.now()
      where telegram_user_id = p_telegram_user_id returning * into v_account;
    insert into public.fortunis8_events (telegram_user_id, event_type, diamond_delta, idempotency_key, metadata)
      values (p_telegram_user_id, 'daily_reward', v_reward,
        'daily:' || p_telegram_user_id::text || ':' || v_today::text,
        pg_catalog.jsonb_build_object('streak', v_streak))
      on conflict (idempotency_key) do nothing;
    return pg_catalog.jsonb_build_object('ok', true, 'claimed', true,
        'diamonds', v_account.diamonds, 'streak', v_account.streak_count, 'reward', v_reward);
end;
$$;

create or replace function public.fortunis8_complete_game(p_session_id uuid, p_telegram_user_id bigint, p_answer text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_game public.fortunis8_game_sessions%rowtype;
    v_diamonds integer;
begin
    select * into v_game from public.fortunis8_game_sessions
      where id = p_session_id and telegram_user_id = p_telegram_user_id for update;
    if not found then return pg_catalog.jsonb_build_object('ok', false, 'reason', 'not_found'); end if;
    if v_game.completed_at is not null then
        return pg_catalog.jsonb_build_object('ok', true, 'completed', true, 'correct', coalesce(v_game.was_correct, false), 'reward', 0);
    end if;
    if v_game.expires_at <= pg_catalog.now() then
        update public.fortunis8_game_sessions set completed_at = pg_catalog.now(), was_correct = false where id = p_session_id;
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'expired');
    end if;
    if pg_catalog.lower(pg_catalog.btrim(coalesce(p_answer, ''))) = pg_catalog.lower(pg_catalog.btrim(v_game.correct_answer)) then
        update public.fortunis8_game_sessions set completed_at = pg_catalog.now(), was_correct = true where id = p_session_id;
        update public.fortunis8_accounts set diamonds = diamonds + v_game.reward_diamonds,
            level = greatest(1, 1 + ((diamonds + v_game.reward_diamonds) / 50)), updated_at = pg_catalog.now()
          where telegram_user_id = p_telegram_user_id returning diamonds into v_diamonds;
        insert into public.fortunis8_events (telegram_user_id, event_type, diamond_delta, idempotency_key, metadata)
          values (p_telegram_user_id, 'game_reward', v_game.reward_diamonds, 'game:' || p_session_id::text,
            pg_catalog.jsonb_build_object('difficulty', v_game.difficulty, 'game_key', v_game.game_key))
          on conflict (idempotency_key) do nothing;
        return pg_catalog.jsonb_build_object('ok', true, 'completed', true, 'correct', true,
            'reward', v_game.reward_diamonds, 'diamonds', v_diamonds);
    end if;
    update public.fortunis8_game_sessions set completed_at = pg_catalog.now(), was_correct = false where id = p_session_id;
    return pg_catalog.jsonb_build_object('ok', true, 'completed', true, 'correct', false, 'reward', 0);
end;
$$;

create or replace function public.fortunis8_claim_charity_quest(p_telegram_user_id bigint, p_quest_key text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_today date := (pg_catalog.now() at time zone 'UTC')::date;
    v_key text;
    v_reward integer := 3;
    v_diamonds integer;
begin
    if p_quest_key not in ('kindness', 'gratitude', 'helpful') then
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'invalid_quest');
    end if;
    insert into public.fortunis8_accounts (telegram_user_id)
      values (p_telegram_user_id) on conflict (telegram_user_id) do nothing;
    v_key := 'quest:' || p_telegram_user_id::text || ':' || p_quest_key || ':' || v_today::text;
    insert into public.fortunis8_events (telegram_user_id, event_type, diamond_delta, idempotency_key, metadata)
      values (p_telegram_user_id, 'charity_quest', v_reward, v_key,
        pg_catalog.jsonb_build_object('quest_key', p_quest_key)) on conflict (idempotency_key) do nothing;
    if not found then
        select diamonds into v_diamonds from public.fortunis8_accounts where telegram_user_id = p_telegram_user_id;
        return pg_catalog.jsonb_build_object('ok', true, 'claimed', false, 'reward', 0, 'diamonds', v_diamonds);
    end if;
    update public.fortunis8_accounts set diamonds = diamonds + v_reward,
        level = greatest(1, 1 + ((diamonds + v_reward) / 50)), updated_at = pg_catalog.now()
      where telegram_user_id = p_telegram_user_id returning diamonds into v_diamonds;
    return pg_catalog.jsonb_build_object('ok', true, 'claimed', true, 'reward', v_reward, 'diamonds', v_diamonds);
end;
$$;

create or replace function public.fortunis8_consume_premium_credit(p_telegram_user_id bigint)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_credits integer;
begin
    update public.fortunis8_accounts set premium_reading_credits = premium_reading_credits - 1,
        updated_at = pg_catalog.now()
      where telegram_user_id = p_telegram_user_id and premium_reading_credits > 0
      returning premium_reading_credits into v_credits;
    if not found then return pg_catalog.jsonb_build_object('ok', false, 'reason', 'no_credit'); end if;
    insert into public.fortunis8_events (telegram_user_id, event_type, diamond_delta, idempotency_key, metadata)
      values (p_telegram_user_id, 'premium_use', 0,
        'premium-use:' || p_telegram_user_id::text || ':' || pg_catalog.gen_random_uuid()::text,
        pg_catalog.jsonb_build_object('credits_remaining', v_credits));
    return pg_catalog.jsonb_build_object('ok', true, 'credits_remaining', v_credits);
end;
$$;

create or replace function public.fortunis8_record_star_payment(
    p_telegram_user_id bigint, p_invoice_payload text, p_charge_id text,
    p_amount integer, p_currency text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_pending public.fortunis8_pending_invoices%rowtype;
    v_existing public.fortunis8_star_payments%rowtype;
    v_credits integer;
begin
    select * into v_existing from public.fortunis8_star_payments
      where telegram_payment_charge_id = p_charge_id or invoice_payload = p_invoice_payload;
    if found then
        return pg_catalog.jsonb_build_object('ok', true, 'credited', false, 'duplicate', true,
            'focus', v_existing.focus, 'credits', null);
    end if;
    select * into v_pending from public.fortunis8_pending_invoices
      where invoice_payload = p_invoice_payload for update;
    if not found or v_pending.telegram_user_id <> p_telegram_user_id
       or v_pending.expires_at <= pg_catalog.now() or v_pending.amount_stars <> p_amount
       or p_currency <> 'XTR' then
        return pg_catalog.jsonb_build_object('ok', false, 'credited', false, 'reason', 'invalid_payment');
    end if;
    insert into public.fortunis8_star_payments (
        telegram_payment_charge_id, invoice_payload, telegram_user_id, product, focus, total_amount, currency
    ) values (p_charge_id, p_invoice_payload, p_telegram_user_id, v_pending.product,
        v_pending.focus, p_amount, p_currency);
    update public.fortunis8_accounts set premium_reading_credits = premium_reading_credits + 1,
        updated_at = pg_catalog.now()
      where telegram_user_id = p_telegram_user_id returning premium_reading_credits into v_credits;
    insert into public.fortunis8_events (telegram_user_id, event_type, diamond_delta, idempotency_key, metadata)
      values (p_telegram_user_id, 'star_purchase', 0, 'star:' || p_charge_id,
        pg_catalog.jsonb_build_object('product', v_pending.product, 'focus', v_pending.focus, 'stars', p_amount));
    delete from public.fortunis8_pending_invoices where invoice_payload = p_invoice_payload;
    return pg_catalog.jsonb_build_object('ok', true, 'credited', true, 'duplicate', false,
        'focus', v_pending.focus, 'credits', v_credits);
end;
$$;

create or replace function public.fortunis8_get_rank(p_telegram_user_id bigint)
returns integer
language sql
stable
security definer
set search_path = ''
as $$
    select ranked.rank::integer from (
        select telegram_user_id, pg_catalog.dense_rank() over (order by diamonds desc)::integer as rank
        from public.fortunis8_accounts
    ) as ranked where ranked.telegram_user_id = p_telegram_user_id
$$;

revoke all on function public.fortunis8_claim_daily(bigint) from public, anon, authenticated;
revoke all on function public.fortunis8_complete_game(uuid, bigint, text) from public, anon, authenticated;
revoke all on function public.fortunis8_claim_charity_quest(bigint, text) from public, anon, authenticated;
revoke all on function public.fortunis8_consume_premium_credit(bigint) from public, anon, authenticated;
revoke all on function public.fortunis8_record_star_payment(bigint, text, text, integer, text) from public, anon, authenticated;
revoke all on function public.fortunis8_get_rank(bigint) from public, anon, authenticated;
grant execute on function public.fortunis8_claim_daily(bigint) to service_role;
grant execute on function public.fortunis8_complete_game(uuid, bigint, text) to service_role;
grant execute on function public.fortunis8_claim_charity_quest(bigint, text) to service_role;
grant execute on function public.fortunis8_consume_premium_credit(bigint) to service_role;
grant execute on function public.fortunis8_record_star_payment(bigint, text, text, integer, text) to service_role;
grant execute on function public.fortunis8_get_rank(bigint) to service_role;

commit;

-- Atomic premium entitlement redemption: consume one purchased credit and persist
-- its reading in one transaction, so a retry cannot lose or duplicate a credit.
create or replace function public.fortunis8_redeem_premium_reading(
    p_telegram_user_id bigint, p_focus text, p_title text, p_content text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_account public.fortunis8_accounts%rowtype;
    v_reading_id uuid;
begin
    if p_focus not in ('general', 'love', 'work', 'growth') then
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'invalid_focus');
    end if;
    select * into v_account from public.fortunis8_accounts
      where telegram_user_id = p_telegram_user_id for update;
    if not found or v_account.premium_reading_credits < 1 then
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'no_credit');
    end if;
    update public.fortunis8_accounts set premium_reading_credits = premium_reading_credits - 1,
        updated_at = pg_catalog.now()
      where telegram_user_id = p_telegram_user_id;
    insert into public.fortunis8_readings (telegram_user_id, reading_type, title, content, metadata)
      values (p_telegram_user_id, 'palm_premium', p_title, p_content,
        pg_catalog.jsonb_build_object('focus', p_focus, 'source', 'telegram_stars'))
      returning id into v_reading_id;
    insert into public.fortunis8_events (telegram_user_id, event_type, diamond_delta, idempotency_key, metadata)
      values (p_telegram_user_id, 'premium_use', 0,
        'premium-reading:' || v_reading_id::text,
        pg_catalog.jsonb_build_object('focus', p_focus, 'reading_id', v_reading_id));
    return pg_catalog.jsonb_build_object('ok', true, 'reading_id', v_reading_id,
        'credits_remaining', v_account.premium_reading_credits - 1);
end;
$$;
revoke all on function public.fortunis8_redeem_premium_reading(bigint, text, text, text) from public, anon, authenticated;
grant execute on function public.fortunis8_redeem_premium_reading(bigint, text, text, text) to service_role;
