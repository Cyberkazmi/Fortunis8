-- Fortunis8 Step 1: persist only Telegram user ID and language preference.
-- Apply this migration to the intended Supabase project before deployment.

begin;

create table if not exists public.fortunis8_users (
    telegram_user_id bigint primary key check (telegram_user_id > 0),
    language text not null default 'en' check (language in ('en', 'ur')),
    created_at timestamptz not null default pg_catalog.now(),
    updated_at timestamptz not null default pg_catalog.now()
);

comment on table public.fortunis8_users is
    'Fortunis8 Step 1: Telegram user language preference only.';

alter table public.fortunis8_users enable row level security;

-- Client roles receive no access. The bot server uses a Supabase secret key,
-- which maps to service_role and must remain in deployment secret storage.
revoke all on table public.fortunis8_users from anon, authenticated;
grant select, insert, update on table public.fortunis8_users to service_role;

create or replace function public.fortunis8_set_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog
as $$
begin
    new.updated_at := pg_catalog.now();
    return new;
end;
$$;

drop trigger if exists fortunis8_users_set_updated_at on public.fortunis8_users;
create trigger fortunis8_users_set_updated_at
before update on public.fortunis8_users
for each row execute function public.fortunis8_set_updated_at();

commit;
