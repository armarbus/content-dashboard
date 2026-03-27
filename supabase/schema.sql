-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Reels table
create table if not exists reels (
  reel_id            text primary key,
  is_own_account     boolean not null default false,
  scraped_at         timestamptz not null default now(),
  competitor_handle  text not null,
  video_url          text,
  thumbnail_url      text,
  caption            text,
  hook               text,
  hook_type          text check (hook_type in ('identiteit','tegenstelling','discipline','transformatie','lifestyle','anders')),
  theme              text check (theme in ('hybrid','kracht','voeding','mindset','lifestyle','anders')),
  views              integer default 0,
  likes              integer default 0,
  comments           integer default 0,
  posted_at          timestamptz,
  viral_score        integer check (viral_score >= 0 and viral_score <= 100),
  ai_why             text,
  ai_your_version    text,
  week_start_date    date not null
);

-- Summaries table
create table if not exists summaries (
  week_start_date  date primary key,
  generated_at     timestamptz not null default now(),
  trending_themes  text,
  best_hook_types  text,
  top3_to_copy     text,
  weekly_advice    text
);

-- Indexes for common queries
create index if not exists idx_reels_week on reels(week_start_date);
create index if not exists idx_reels_handle on reels(competitor_handle);
create index if not exists idx_reels_score on reels(viral_score desc);
create index if not exists idx_reels_own on reels(is_own_account);

-- Enable Row Level Security
alter table reels enable row level security;
alter table summaries enable row level security;

-- Allow anon (Streamlit dashboard) to read only
create policy "anon read reels" on reels
  for select to anon using (true);

create policy "anon read summaries" on summaries
  for select to anon using (true);

-- Allow service_role (GitHub Actions processor) full access (default: already has it)
