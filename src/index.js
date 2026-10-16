// Worker 진입점 (wrangler.toml의 main).
//
// 기존 "functions/api/leaderboard.js"는 Cloudflare Pages Functions 전용 규칙
// (functions/ 폴더 자동 라우팅)이라, 이 레포가 "Workers" 배포(npx wrangler deploy)로
// 전환되면서 더 이상 자동으로 인식되지 않았다. 그래서 여기서 직접 라우팅하고,
// 그 외 모든 경로는 정적 자산(ASSETS 바인딩)으로 넘긴다.
//
// functions/api/leaderboard.js 자체는 수정하지 않고 그대로 재사용한다
// (onRequestGet/onRequestPost가 받는 {request, env} 형태만 맞춰주면 된다).

import { onRequestGet, onRequestPost } from "../functions/api/leaderboard.js";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/api/leaderboard") {
      if (request.method === "GET") return onRequestGet({ request, env, ctx });
      if (request.method === "POST") return onRequestPost({ request, env, ctx });
      return new Response("Method Not Allowed", { status: 405, headers: { Allow: "GET, POST" } });
    }

    return env.ASSETS.fetch(request);
  },
};
