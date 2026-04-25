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

-- ─── Pokémon Reference Data (populated by ingestion script) ─────────────────
-- No RLS: public read-only reference tables

create table if not exists public.pokemon (
  id                      integer primary key,
  name                    text not null,
  generation              integer not null,
  height                  integer,
  weight                  integer,
  base_experience         integer,
  -- Base stats (inlined — always fetched together, avoids join on hot paths)
  hp                      integer not null,
  attack                  integer not null,
  defense                 integer not null,
  special_attack          integer not null,
  special_defense         integer not null,
  speed                   integer not null,
  -- Species display
  is_legendary            boolean not null default false,
  is_mythical             boolean not null default false,
  color                   text,
  capture_rate            integer,
  base_happiness          integer,
  flavor_text             text,
  genus                   text,
  evolution_chain_id      integer,
  -- Sprites (inlined — needed on list pages to avoid extra join)
  sprite_front            text,
  sprite_official_artwork text,
  sprite_shiny            text,
  sprite_home             text
);

create table if not exists public.pokemon_types (
  pokemon_id  integer not null references public.pokemon(id) on delete cascade,
  type_name   text not null,
  slot        integer not null,
  primary key (pokemon_id, slot)
);

create table if not exists public.pokemon_abilities (
  pokemon_id    integer not null references public.pokemon(id) on delete cascade,
  ability_name  text not null,
  is_hidden     boolean not null default false,
  slot          integer not null,
  primary key (pokemon_id, slot)
);

create table if not exists public.moves (
  id            integer primary key,
  name          text not null unique,
  power         integer,
  accuracy      integer,
  pp            integer not null,
  type          text not null,
  damage_class  text not null,
  flavor_text   text
);

create table if not exists public.pokemon_learnable_moves (
  pokemon_id    integer not null references public.pokemon(id) on delete cascade,
  move_id       integer not null references public.moves(id) on delete cascade,
  learn_method  text not null,
  min_level     integer,
  primary key (pokemon_id, move_id, learn_method)
);

create table if not exists public.abilities (
  name          text primary key,
  short_effect  text,
  effect        text
);

create table if not exists public.natures (
  name            text primary key,
  increased_stat  text,
  decreased_stat  text
);

create table if not exists public.items (
  id          integer primary key,
  name        text not null unique,
  sprite_url  text,
  category    text,
  flavor_text text
);

-- Evolution chains stored as a flat ordered JSON array [{id, name}, ...]
-- Rationale: PokéAPI chains are variable-depth trees; frontend only needs a
-- flat strip of evolution family members. JSONB avoids a self-referential table.
create table if not exists public.evolution_chains (
  id     integer primary key,
  chain  jsonb not null default '[]'::jsonb
);

-- Pokémon alternate forms (Alolan, Galarian, Mega, style variants, etc.)
-- species_id    → the base/default Pokémon (e.g. 75 for Graveler)
-- form_pokemon_id → the variant's own PokéAPI ID (e.g. 10032 for Alolan Graveler)
-- Both varieties (including the default) are listed here so the frontend can
-- show a complete form selector. Only rows exist when a species has >1 form.
create table if not exists public.pokemon_varieties (
  species_id       integer not null,
  form_pokemon_id  integer not null,
  form_name        text    not null,   -- full PokéAPI name: "graveler-alola"
  form_suffix      text    not null,   -- URL param value:  "alola"  (empty for default)
  display_name     text    not null,   -- human label:      "Alolan" ("Default" for base)
  is_default       boolean not null default false,
  primary key (species_id, form_pokemon_id),
  constraint pv_species_fk foreign key (species_id)      references public.pokemon(id) on delete cascade,
  constraint pv_form_fk    foreign key (form_pokemon_id) references public.pokemon(id) on delete cascade
);

create index if not exists pokemon_varieties_species_idx on public.pokemon_varieties(species_id);

create index if not exists pokemon_types_pokemon_id_idx on public.pokemon_types(pokemon_id);
create index if not exists pokemon_types_type_name_idx  on public.pokemon_types(type_name);
create index if not exists pokemon_abilities_pokemon_id_idx on public.pokemon_abilities(pokemon_id);
create index if not exists pokemon_learnable_moves_pokemon_id_idx on public.pokemon_learnable_moves(pokemon_id);
create index if not exists pokemon_generation_idx on public.pokemon(generation);

-- FK from pokemon → evolution_chains (must be added after both tables exist)
-- PostgREST requires this to perform the embedded join in GET /pokemon/{id}
do $$
begin
  if not exists (
    select 1 from information_schema.table_constraints
    where constraint_name = 'fk_pokemon_evolution_chain'
      and table_name = 'pokemon'
      and table_schema = 'public'
  ) then
    alter table public.pokemon
      add constraint fk_pokemon_evolution_chain
      foreign key (evolution_chain_id) references public.evolution_chains(id);
  end if;
end$$;
