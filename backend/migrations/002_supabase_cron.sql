-- =============================================================================
-- Supabase Cron — 매일 00:00 KST (UTC 15:00) today_earned 리셋
-- Supabase Dashboard → Database → Extensions 에서 pg_cron 활성화 후 실행
-- =============================================================================

select cron.schedule(
  'reset-today-earned',
  '0 15 * * *',           -- 매일 UTC 15:00 = KST 00:00
  $$ select public.reset_today_earned(); $$
);
