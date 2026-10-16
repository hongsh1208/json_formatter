// Cloudflare Pages Function: /api/leaderboard
//
// 타자 속도 테스트의 공개 랭킹 API. Cloudflare D1 바인딩(env.DB, 바인딩 이름 "DB")이
// Pages 프로젝트에 연결돼 있어야 동작한다. 설정 방법은 scripts/d1-schema.sql 상단 주석과
// README.md의 "랭킹(리더보드) 설정" 절 참고.
//
// GET  /api/leaderboard?lang=ko&limit=20  → 해당 언어의 WPM 상위 기록 목록 반환
// POST /api/leaderboard  { nickname, wpm, accuracy, lang }  → 기록 1건 제출
//
// 개인정보 최소화: IP 주소는 원문으로 저장하지 않고, 스팸 방지용 빈도 제한을 위해
// 솔트를 섞어 SHA-256 해시한 값만 짧게 보관한다 (privacy.html 1-3절에 안내됨).
//
// 랭킹은 "월간" 랭킹이다 — 기록 자체는 DB에서 지우지 않고(히스토리 보존), 조회/순위
// 계산 시 이번 달(한국 시간 KST, UTC+9 기준) 1일 00:00 이후의 기록만 포함시키는
// 방식으로 매월 자동 초기화되는 것처럼 동작시킨다. 다음 초기화 시각(resetAt)도
// 함께 내려줘서 프런트엔드가 D-day 카운트다운을 표시할 수 있게 한다.

const ALLOWED_LANGS = ["en", "ko", "ja", "zh", "es", "vi", "pt", "id", "de"];
const RATE_LIMIT_MS = 10000; // 같은 IP에서 10초 이내 재제출 차단
const MAX_LIMIT = 50;
const DEFAULT_LIMIT = 20;
const KST_OFFSET_MS = 9 * 60 * 60 * 1000;

function monthBoundaryKst(now) {
  // now(UTC 기준 Date)를 KST 벽시계 기준으로 봤을 때, 그 달의 1일 00:00(KST)과
  // 다음 달 1일 00:00(KST)을 각각 실제 UTC 시각(ISO 문자열)으로 변환해 반환한다.
  const kstWall = new Date(now.getTime() + KST_OFFSET_MS);
  const y = kstWall.getUTCFullYear();
  const m = kstWall.getUTCMonth();
  const startUtcMs = Date.UTC(y, m, 1, 0, 0, 0) - KST_OFFSET_MS;
  const nextUtcMs = Date.UTC(y, m + 1, 1, 0, 0, 0) - KST_OFFSET_MS;
  return {
    startIso: new Date(startUtcMs).toISOString(),
    resetAtIso: new Date(nextUtcMs).toISOString(),
  };
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

async function hashIp(ip, salt) {
  const enc = new TextEncoder().encode(ip + "|" + salt);
  const digest = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function sanitizeNickname(raw) {
  let name = typeof raw === "string" ? raw : "";
  // 제어문자 및 HTML 특수문자 제거, 공백 정리, 길이 제한
  name = name.replace(/[\u0000-\u001F\u007F<>&"']/g, "").trim();
  name = name.slice(0, 20);
  return name || "Anonymous";
}

export async function onRequestGet(context) {
  const { request, env } = context;
  if (!env.DB) {
    return jsonResponse({ error: "leaderboard_not_configured" }, 503);
  }
  const url = new URL(request.url);
  const lang = (url.searchParams.get("lang") || "en").slice(0, 2).toLowerCase();
  if (!ALLOWED_LANGS.includes(lang)) {
    return jsonResponse({ error: "invalid_lang" }, 400);
  }
  let limit = parseInt(url.searchParams.get("limit") || String(DEFAULT_LIMIT), 10);
  if (!Number.isFinite(limit) || limit < 1) limit = DEFAULT_LIMIT;
  limit = Math.min(limit, MAX_LIMIT);

  const { startIso, resetAtIso } = monthBoundaryKst(new Date());

  try {
    const { results } = await env.DB.prepare(
      "SELECT nickname, wpm, accuracy, created_at FROM scores WHERE lang = ?1 AND created_at >= ?2 ORDER BY wpm DESC, accuracy DESC, created_at ASC LIMIT ?3"
    )
      .bind(lang, startIso, limit)
      .all();
    return jsonResponse({ entries: results || [], resetAt: resetAtIso });
  } catch (err) {
    return jsonResponse({ error: "query_failed" }, 500);
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.DB) {
    return jsonResponse({ error: "leaderboard_not_configured" }, 503);
  }

  let body;
  try {
    body = await request.json();
  } catch (err) {
    return jsonResponse({ error: "invalid_json" }, 400);
  }

  const lang = typeof body.lang === "string" ? body.lang.slice(0, 2).toLowerCase() : "";
  if (!ALLOWED_LANGS.includes(lang)) {
    return jsonResponse({ error: "invalid_lang" }, 400);
  }

  const wpm = Math.round(Number(body.wpm));
  const accuracy = Math.round(Number(body.accuracy));
  if (!Number.isFinite(wpm) || wpm < 1 || wpm > 400) {
    return jsonResponse({ error: "invalid_wpm" }, 400);
  }
  if (!Number.isFinite(accuracy) || accuracy < 0 || accuracy > 100) {
    return jsonResponse({ error: "invalid_accuracy" }, 400);
  }

  const nickname = sanitizeNickname(body.nickname);
  const salt = env.LEADERBOARD_SALT || "formix-typing-leaderboard";
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ipHash = await hashIp(ip, salt);
  const nowDate = new Date();
  const now = nowDate.getTime();
  const { startIso, resetAtIso } = monthBoundaryKst(nowDate);

  try {
    const recent = await env.DB.prepare(
      "SELECT created_at FROM scores WHERE ip_hash = ?1 ORDER BY created_at DESC LIMIT 1"
    )
      .bind(ipHash)
      .first();
    if (recent && now - Date.parse(recent.created_at) < RATE_LIMIT_MS) {
      return jsonResponse({ error: "rate_limited" }, 429);
    }

    const createdAt = new Date(now).toISOString();
    await env.DB.prepare(
      "INSERT INTO scores (nickname, wpm, accuracy, lang, created_at, ip_hash) VALUES (?1, ?2, ?3, ?4, ?5, ?6)"
    )
      .bind(nickname, wpm, accuracy, lang, createdAt, ipHash)
      .run();

    const rankRow = await env.DB.prepare(
      "SELECT COUNT(*) AS cnt FROM scores WHERE lang = ?1 AND wpm > ?2 AND created_at >= ?3"
    )
      .bind(lang, wpm, startIso)
      .first();
    const rank = (rankRow && rankRow.cnt ? rankRow.cnt : 0) + 1;

    return jsonResponse({ ok: true, rank, nickname, wpm, accuracy, resetAt: resetAtIso });
  } catch (err) {
    return jsonResponse({ error: "insert_failed" }, 500);
  }
}
