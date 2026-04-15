-- KantoVision: Supabase database schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New Query)

create table if not exists public.teams (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  name        text not null,
  slots       jsonb not null default '[]'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Auto-update updated_at on row changes
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog
as $$
begin
  new.updated_at = pg_catalog.now();
  return new;
end;
$$;

create or replace trigger teams_updated_at
  before update on public.teams
  for each row execute function public.set_updated_at();

-- Row Level Security: users can only see/modify their own teams
alter table public.teams enable row level security;

create policy "Users can read own teams"
  on public.teams for select
  using (auth.uid() = user_id);

create policy "Users can insert own teams"
  on public.teams for insert
  with check (auth.uid() = user_id);

create policy "Users can update own teams"
  on public.teams for update
  using (auth.uid() = user_id);

create policy "Users can delete own teams"
  on public.teams for delete
  using (auth.uid() = user_id);

-- Index for fast per-user lookups
create index if not exists teams_user_id_idx on public.teams(user_id);

-- ─── Profiles ────────────────────────────────────────────────────────────────

create table if not exists public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  username     text unique not null
                 check (username ~ '^[a-zA-Z0-9_]{3,20}$'),
  display_name text,
  created_at   timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles readable by all"
  on public.profiles for select using (true);

create policy "profiles writable by owner"
  on public.profiles for all using (auth.uid() = id);

create index if not exists profiles_username_idx on public.profiles(username);

-- ─── Battles ─────────────────────────────────────────────────────────────────

create table if not exists public.battles (
  id          uuid primary key default gen_random_uuid(),
  player1_id  uuid not null references auth.users(id),
  player2_id  uuid not null references auth.users(id),
  winner_id   uuid references auth.users(id),
  turns       int not null default 0,
  created_at  timestamptz not null default now()
);

alter table public.battles enable row level security;

create policy "battles readable by participants"
  on public.battles for select
  using (auth.uid() = player1_id or auth.uid() = player2_id);

create index if not exists battles_player1_idx on public.battles(player1_id);
create index if not exists battles_player2_idx on public.battles(player2_id);

-- ─── Run in Supabase SQL Editor to apply schema ───────────────────────────────
-- (The battles table above replaces the old one; run this if migrating)
-- drop table if exists public.pokemon_usage;
-- drop table if exists public.friendships;
