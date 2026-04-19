-- 004_add_image_urls.sql
-- topics 테이블에 여러 이미지 URL을 저장하는 컬럼 추가
ALTER TABLE topics ADD COLUMN IF NOT EXISTS image_urls_json TEXT;
