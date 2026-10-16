// 방명록 API. Cloudflare D1 바인딩(env.DB, 바인딩 이름 "DB")이 필요하다 — 타자 속도
// 테스트 랭킹(functions/api/leaderboard.js)과 같은 D1 데이터베이스를 공유하되, 별도
// 테이블(guestbook)을 쓴다. 스키마는 scripts/d1-schema.sql 참고.
//
// GET  /api/guestbook?limit=30  → 최근 메시지 목록 (언어 구분 없이 전체 공용)
// POST /api/guestbook { nickname, message }  → 한 줄 메시지 1건 등록
//
// 개인정보 최소화: IP 주소는 원문으로 저장하지 않고, 스팸 방지용 빈도 제한을 위해
// 솔트를 섞어 SHA-256 해시한 값만 짧게 보관한다 (privacy.html 참고).

const MAX_LIMIT = 50;
const DEFAULT_LIMIT = 30;
const RATE_LIMIT_MS = 10000; // 같은 IP에서 10초 이내 재게시 차단
const MAX_MESSAGE_LEN = 100;
const MAX_NICKNAME_LEN = 20;

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
  name = name.replace(/[\u0000-\u001F\u007F<>&"']/g, "").trim();
  name = name.slice(0, MAX_NICKNAME_LEN);
  return name || "Anonymous";
}

function sanitizeMessage(raw) {
  let msg = typeof raw === "string" ? raw : "";
  // 한 줄만 허용 — 줄바꿈은 공백으로 치환하고, 제어문자/HTML 특수문자는 제거한다.
  msg = msg.replace(/[\r\n]+/g, " ");
  msg = msg.replace(/[\u0000-\u001F\u007F<>&"']/g, "").trim();
  msg = msg.slice(0, MAX_MESSAGE_LEN);
  return msg;
}

export async function onRequestGet(context) {
  const { request, env } = context;
  if (!env.DB) {
    return jsonResponse({ error: "guestbook_not_configured" }, 503);
  }
  const url = new URL(request.url);
  let limit = parseInt(url.searchParams.get("limit") || String(DEFAULT_LIMIT), 10);
  if (!Number.isFinite(limit) || limit < 1) limit = DEFAULT_LIMIT;
  limit = Math.min(limit, MAX_LIMIT);

  try {
    const { results } = await env.DB.prepare(
      "SELECT nickname, message, created_at FROM guestbook ORDER BY created_at DESC LIMIT ?1"
    )
      .bind(limit)
      .all();
    return jsonResponse({ entries: results || [] });
  } catch (err) {
    return jsonResponse({ error: "query_failed" }, 500);
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.DB) {
    return jsonResponse({ error: "guestbook_not_configured" }, 503);
  }

  let body;
  try {
    body = await request.json();
  } catch (err) {
    return jsonResponse({ error: "invalid_json" }, 400);
  }

  const message = sanitizeMessage(body.message);
  if (!message) {
    return jsonResponse({ error: "invalid_message" }, 400);
  }
  const nickname = sanitizeNickname(body.nickname);

  const salt = env.GUESTBOOK_SALT || "formix-guestbook";
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ipHash = await hashIp(ip, salt);
  const now = Date.now();

  try {
    const recent = await env.DB.prepare(
      "SELECT created_at FROM guestbook WHERE ip_hash = ?1 ORDER BY created_at DESC LIMIT 1"
    )
      .bind(ipHash)
      .first();
    if (recent && now - Date.parse(recent.created_at) < RATE_LIMIT_MS) {
      return jsonResponse({ error: "rate_limited" }, 429);
    }

    const createdAt = new Date(now).toISOString();
    await env.DB.prepare(
      "INSERT INTO guestbook (nickname, message, created_at, ip_hash) VALUES (?1, ?2, ?3, ?4)"
    )
      .bind(nickname, message, createdAt, ipHash)
      .run();

    return jsonResponse({ ok: true, nickname, message });
  } catch (err) {
    return jsonResponse({ error: "insert_failed" }, 500);
  }
}
