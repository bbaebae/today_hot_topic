-- =============================================================================
-- 오늘 왜 떠? — 초기 Supabase 스키마
-- Supabase SQL Editor에서 실행하세요.
-- =============================================================================

-- UUID 확장 (Supabase 기본 활성화)
create extension if not exists "uuid-ossp";

-- -----------------------------------------------------------------------------
-- users
-- -----------------------------------------------------------------------------
create table if not exists public.users (
  id              uuid primary key default uuid_generate_v4(),
  toss_user_id    text not null unique,          -- Toss Bridge가 전달하는 익명 ID
  is_premium      boolean not null default false,
  total_points    integer not null default 0,
  today_earned    integer not null default 0,    -- 매일 00:00 KST에 리셋
  created_at      timestamptz not null default now()
);

-- daily_earned 리셋 함수 (Supabase Cron으로 00:00 KST = 15:00 UTC 실행)
create or replace function public.reset_today_earned()
returns void language sql as $$
  update public.users set today_earned = 0;
$$;

-- -----------------------------------------------------------------------------
-- topics
-- -----------------------------------------------------------------------------
create table if not exists public.topics (
  id              uuid primary key default uuid_generate_v4(),
  title           text not null,
  category        text not null check (category in ('news', 'story', 'finance')),
  source          text not null,                -- 'pann' | 'dcinside' | 'fmkorea'
  external_id     text not null,               -- 원본 글 ID
  source_url      text not null,
  image_url       text,
  view_count      integer not null default 0,
  rank            integer not null default 9999,
  summary_json    text,                        -- JSON array string ["줄1","줄2","줄3"]
  created_at      timestamptz not null default now(),

  unique (source, external_id)
);

create index if not exists idx_topics_category_rank on public.topics (category, rank);
create index if not exists idx_topics_view_count     on public.topics (view_count desc);
create index if not exists idx_topics_created_at     on public.topics (created_at desc);

-- view_count 원자적 증가 (HTTP 중복 호출 방어)
create or replace function public.increment_view_count(topic_id uuid)
returns void language sql as $$
  update public.topics
  set view_count = view_count + 1
  where id = topic_id;
$$;

-- -----------------------------------------------------------------------------
-- polls
-- -----------------------------------------------------------------------------
create table if not exists public.polls (
  id              uuid primary key default uuid_generate_v4(),
  topic_id        uuid not null references public.topics (id) on delete cascade,
  option_a_text   text not null default '찬성',
  option_b_text   text not null default '반대',
  option_a_count  integer not null default 0,
  option_b_count  integer not null default 0,
  created_at      timestamptz not null default now(),

  unique (topic_id)
);

create index if not exists idx_polls_topic_id on public.polls (topic_id);

-- -----------------------------------------------------------------------------
-- vote_logs  (idempotency 보장 — 동일 user + poll 중복 투표 방지)
-- -----------------------------------------------------------------------------
create table if not exists public.vote_logs (
  id              uuid primary key default uuid_generate_v4(),
  poll_id         uuid not null references public.polls (id) on delete cascade,
  user_id         uuid not null references public.users (id) on delete cascade,
  selected_option text not null check (selected_option in ('A', 'B')),
  created_at      timestamptz not null default now(),

  unique (poll_id, user_id)
);

create index if not exists idx_vote_logs_user_id on public.vote_logs (user_id);

-- -----------------------------------------------------------------------------
-- point_transactions
-- -----------------------------------------------------------------------------
create table if not exists public.point_transactions (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users (id) on delete cascade,
  amount          integer not null,
  reason          text not null check (reason in ('vote', 'ad', 'share')),
  reference_id    text,                        -- poll_id 또는 광고 ID 등
  status          text not null default 'pending'
                    check (status in ('pending', 'success', 'failed')),
  created_at      timestamptz not null default now()
);

create index if not exists idx_pt_user_id    on public.point_transactions (user_id);
create index if not exists idx_pt_created_at on public.point_transactions (created_at desc);

-- -----------------------------------------------------------------------------
-- Row Level Security (RLS) — service_role 키만 전체 접근 허용
-- 클라이언트 anon 키로는 직접 접근 차단
-- -----------------------------------------------------------------------------
alter table public.users              enable row level security;
alter table public.topics             enable row level security;
alter table public.polls              enable row level security;
alter table public.vote_logs          enable row level security;
alter table public.point_transactions enable row level security;

-- service_role 전체 허용 (FastAPI 백엔드용)
create policy "service_role_all" on public.users
  for all using (auth.role() = 'service_role');
create policy "service_role_all" on public.topics
  for all using (auth.role() = 'service_role');
create policy "service_role_all" on public.polls
  for all using (auth.role() = 'service_role');
create policy "service_role_all" on public.vote_logs
  for all using (auth.role() = 'service_role');
create policy "service_role_all" on public.point_transactions
  for all using (auth.role() = 'service_role');

-- topics / polls 읽기는 anon도 허용 (퍼블릭 데이터)
create policy "anon_read_topics" on public.topics
  for select using (true);
create policy "anon_read_polls" on public.polls
  for select using (true);
