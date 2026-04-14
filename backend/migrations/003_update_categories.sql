-- =============================================================================
-- Migration 003: 카테고리 재편 news/story/finance → story/society/economy/sports/love
-- Supabase SQL Editor에서 실행하세요.
-- =============================================================================

-- 1. 기존 CHECK 제약 제거
alter table public.topics drop constraint if exists topics_category_check;

-- 2. 기존 데이터 마이그레이션 (기존 news → society, finance → economy)
update public.topics set category = 'society' where category = 'news';
update public.topics set category = 'economy' where category = 'finance';

-- 3. 새 CHECK 제약 추가
alter table public.topics
  add constraint topics_category_check
  check (category in ('story', 'society', 'economy', 'sports', 'love'));
