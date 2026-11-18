-- Durable Telegram update-idempotency for premium palm-reading redemption.
-- This migration adds only Fortunis8-owned objects; it does not alter existing tables.
begin;

create table if not exists public.fortunis8_premium_redemption_receipts (
    telegram_update_id bigint primary key check (telegram_update_id >= 0),
    telegram_user_id bigint not null,
    focus text not null check (focus in ('general', 'love', 'work', 'growth')),
    outcome text not null default 'processing'
        check (outcome in ('processing', 'redeemed', 'no_credit')),
    reading_id uuid unique,
    credits_remaining integer check (credits_remaining >= 0),
    created_at timestamptz not null default pg_catalog.now(),
    constraint fortunis8_premium_redemption_result_check check (
        (outcome = 'processing' and reading_id is null and credits_remaining is null)
        or (outcome = 'redeemed' and reading_id is not null and credits_remaining is not null)
        or (outcome = 'no_credit' and reading_id is null and credits_remaining is not null)
    )
);

alter table public.fortunis8_premium_redemption_receipts enable row level security;
revoke all on table public.fortunis8_premium_redemption_receipts from anon, authenticated;
grant all on table public.fortunis8_premium_redemption_receipts to service_role;

create or replace function public.fortunis8_redeem_premium_reading_for_update(
    p_telegram_user_id bigint,
    p_telegram_update_id bigint,
    p_focus text,
    p_title text,
    p_content text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_account public.fortunis8_accounts%rowtype;
    v_receipt public.fortunis8_premium_redemption_receipts%rowtype;
    v_receipt_inserted boolean := false;
    v_reading_id uuid;
    v_credits_remaining integer;
begin
    if p_telegram_user_id is null or p_telegram_update_id is null or p_telegram_update_id < 0
       or p_focus is null or p_focus not in ('general', 'love', 'work', 'growth')
       or p_title is null or pg_catalog.length(p_title) > 120
       or p_content is null or pg_catalog.length(p_content) > 3500 then
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'invalid_request');
    end if;

    -- Serializes concurrent deliveries for this account before checking the receipt.
    select * into v_account from public.fortunis8_accounts
      where telegram_user_id = p_telegram_user_id for update;
    if not found then
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'account_missing');
    end if;

    select * into v_receipt from public.fortunis8_premium_redemption_receipts
      where telegram_update_id = p_telegram_update_id for update;
    if found then
        if v_receipt.telegram_user_id <> p_telegram_user_id or v_receipt.focus <> p_focus then
            return pg_catalog.jsonb_build_object('ok', false, 'reason', 'update_conflict');
        end if;
        if v_receipt.outcome = 'redeemed' then
            return pg_catalog.jsonb_build_object(
                'ok', true, 'duplicate', true, 'reading_id', v_receipt.reading_id,
                'credits_remaining', v_receipt.credits_remaining
            );
        elsif v_receipt.outcome = 'no_credit' then
            return pg_catalog.jsonb_build_object(
                'ok', false, 'duplicate', true, 'reason', 'no_credit',
                'credits_remaining', v_receipt.credits_remaining
            );
        else
            -- A processing row is not visible before the transaction commits; fail closed if one exists.
            return pg_catalog.jsonb_build_object('ok', false, 'reason', 'update_in_progress');
        end if;
    end if;

    insert into public.fortunis8_premium_redemption_receipts (
        telegram_update_id, telegram_user_id, focus
    ) values (p_telegram_update_id, p_telegram_user_id, p_focus)
    on conflict (telegram_update_id) do nothing
    returning true into v_receipt_inserted;

    if not coalesce(v_receipt_inserted, false) then
        select * into v_receipt from public.fortunis8_premium_redemption_receipts
          where telegram_update_id = p_telegram_update_id for update;
        if not found or v_receipt.telegram_user_id <> p_telegram_user_id or v_receipt.focus <> p_focus then
            return pg_catalog.jsonb_build_object('ok', false, 'reason', 'update_conflict');
        end if;
        if v_receipt.outcome = 'redeemed' then
            return pg_catalog.jsonb_build_object(
                'ok', true, 'duplicate', true, 'reading_id', v_receipt.reading_id,
                'credits_remaining', v_receipt.credits_remaining
            );
        elsif v_receipt.outcome = 'no_credit' then
            return pg_catalog.jsonb_build_object(
                'ok', false, 'duplicate', true, 'reason', 'no_credit',
                'credits_remaining', v_receipt.credits_remaining
            );
        end if;
        return pg_catalog.jsonb_build_object('ok', false, 'reason', 'update_in_progress');
    end if;

    if v_account.premium_reading_credits < 1 then
        update public.fortunis8_premium_redemption_receipts set
            outcome = 'no_credit', credits_remaining = v_account.premium_reading_credits
          where telegram_update_id = p_telegram_update_id;
        return pg_catalog.jsonb_build_object(
            'ok', false, 'duplicate', false, 'reason', 'no_credit',
            'credits_remaining', v_account.premium_reading_credits
        );
    end if;

    update public.fortunis8_accounts set
        premium_reading_credits = premium_reading_credits - 1,
        updated_at = pg_catalog.now()
      where telegram_user_id = p_telegram_user_id
      returning premium_reading_credits into v_credits_remaining;

    insert into public.fortunis8_readings (
        telegram_user_id, reading_type, title, content, metadata
    ) values (
        p_telegram_user_id, 'palm_premium', p_title, p_content,
        pg_catalog.jsonb_build_object('focus', p_focus, 'source', 'telegram_stars')
    ) returning id into v_reading_id;

    insert into public.fortunis8_events (
        telegram_user_id, event_type, diamond_delta, idempotency_key, metadata
    ) values (
        p_telegram_user_id, 'premium_use', 0,
        'premium-reading:' || v_reading_id::text,
        pg_catalog.jsonb_build_object('focus', p_focus, 'reading_id', v_reading_id,
            'telegram_update_id', p_telegram_update_id)
    );

    update public.fortunis8_premium_redemption_receipts set
        outcome = 'redeemed', reading_id = v_reading_id,
        credits_remaining = v_credits_remaining
      where telegram_update_id = p_telegram_update_id;

    return pg_catalog.jsonb_build_object(
        'ok', true, 'duplicate', false, 'reading_id', v_reading_id,
        'credits_remaining', v_credits_remaining
    );
end;
$$;

revoke all on function public.fortunis8_redeem_premium_reading_for_update(bigint, bigint, text, text, text)
    from public, anon, authenticated;
grant execute on function public.fortunis8_redeem_premium_reading_for_update(bigint, bigint, text, text, text)
    to service_role;

commit;
