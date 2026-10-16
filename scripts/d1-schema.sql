-- Formix 타자 속도 테스트 랭킹용 D1 스키마.
--
-- 적용 방법 (Cloudflare 대시보드에서, wrangler CLI 없이):
--   1. Cloudflare 대시보드 → Workers & Pages → D1 → "Create database" →
--      이름은 자유(예: formix-leaderboard)로 생성.
--   2. 생성된 데이터베이스 → "Console" 탭에서 이 파일 내용을 그대로 붙여넣고 실행.
--   3. Pages 프로젝트(formix.site) → Settings → Functions → D1 database bindings →
--      "Add binding" → Variable name: DB (대문자, functions/api/leaderboard.js의
--      env.DB와 반드시 일치해야 함) → 방금 만든 데이터베이스 선택 → Save.
--   4. (선택) 같은 Settings → Functions → Environment variables에 LEADERBOARD_SALT를
--      임의의 긴 문자열로 추가하면 IP 해시용 솔트가 바뀜 — 설정 안 해도 기본값으로 동작함.
--   5. 바인딩 저장 후에는 Pages 배포를 한 번 다시 트리거해야 함(재배포 또는 "Retry deployment").
--
-- wrangler CLI를 쓴다면:
--   wrangler d1 create formix-leaderboard
--   wrangler d1 execute formix-leaderboard --file=scripts/d1-schema.sql
--   (그리고 wrangler.toml에 d1_databases 바인딩 추가 또는 Pages 프로젝트에 --d1 플래그로 연결)

CREATE TABLE IF NOT EXISTS scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT NOT NULL,
  wpm INTEGER NOT NULL,
  accuracy INTEGER NOT NULL,
  lang TEXT NOT NULL,
  created_at TEXT NOT NULL,
  ip_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_scores_lang_wpm ON scores (lang, wpm DESC);
CREATE INDEX IF NOT EXISTS idx_scores_ip_created ON scores (ip_hash, created_at);
