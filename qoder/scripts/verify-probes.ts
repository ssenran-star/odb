// Reviewer probes for 今天吃什么.
// From qoder/: deno run --allow-env --allow-net scripts/verify-probes.ts
// Optional live PowerContext read: set POWERCONTEXT_URL and POWERCONTEXT_SCOPE_ID.
// Add --write to remember a verification preference and history entry, then search it.

import { isKnownRoute, normalizeApiPath } from "../functions/routing.mjs";
import { serviceConfigFrom } from "../functions/service-config.ts";
import { PowerContextClient } from "../functions/powercontext-client.ts";
import { foods } from "../functions/data.ts";

const routingCases: Array<[string, string]> = [
  ["/functions/v1/app", "/"],
  ["/functions/v1/app/", "/"],
  ["/functions/v1/app/api/foods", "/api/foods"],
  ["/functions/v1/app/api/foods/", "/api/foods"],
  ["/functions/v1/app/api/services/status", "/api/services/status"],
  ["/app", "/"],
  ["/app/", "/"],
  ["/app/api/foods", "/api/foods"],
  ["/app/api/services/status/", "/api/services/status"],
  ["/api/foods", "/api/foods"],
  ["/", "/"],
  ["/v1/app/api/foods/search", "/api/foods/search"],
  ["/functions/v1/app/functions/v1/app/api/user/history", "/api/user/history"],
];

let failed = 0;
for (const [input, expected] of routingCases) {
  const actual = normalizeApiPath(input);
  const known = isKnownRoute(actual);
  if (actual !== expected || !known) {
    console.error(`routing FAIL ${input} -> ${actual} (expected ${expected}, known=${known})`);
    failed += 1;
  }
}
if (failed === 0) {
  console.log(`routing self-check ok (${routingCases.length} paths)`);
}

const configCases: Array<[Record<string, string | undefined>, string]> = [
  [{}, "demo"],
  [{ POWERCONTEXT_URL: "https://example.trycloudflare.com", POWERCONTEXT_SCOPE_ID: "scp_example" }, "powercontext"],
  [{ USE_REAL_SERVICES: "false", POWERCONTEXT_URL: "https://example.trycloudflare.com", POWERCONTEXT_SCOPE_ID: "scp_example" }, "demo"],
  [{ USE_REAL_SERVICES: "true" }, "demo"],
  [{ SEEKDB_HOST: "127.0.0.1" }, "seekdb"],
];
for (const [raw, expected] of configCases) {
  const config = serviceConfigFrom(raw);
  const mode = config.powerContext ? "powercontext" : config.seekdb ? "seekdb" : "demo";
  if (mode !== expected) {
    console.error(`config FAIL ${JSON.stringify(raw)} -> ${mode} (expected ${expected})`);
    failed += 1;
  }
}
if (failed === 0) console.log("service config self-check ok");

const site = "https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone";
console.log(`
Local function (from qoder/, after npm run dev:function):
  curl -sS http://127.0.0.1:8000/functions/v1/app
  curl -sS http://127.0.0.1:8000/functions/v1/app/api/foods
  curl -sS http://127.0.0.1:8000/app/api/services/status
  curl -sS --get --data-urlencode "q=辣" http://127.0.0.1:8000/api/foods/search

Vite dev server proxies the same prefix:
  curl -sS http://127.0.0.1:5173/functions/v1/app/api/services/status

Published site (404 until Qoder Desktop republishes this commit):
  curl -sS ${site}/functions/v1/app
  curl -sS ${site}/functions/v1/app/api/foods
  curl -sS ${site}/functions/v1/app/api/services/status

PowerContext (placeholders only; trycloudflare hostnames rotate):
  POWERCONTEXT_URL=https://cal-ent-altered-higher.trycloudflare.com
  POWERCONTEXT_SCOPE_ID=scp_15fskprdpsyc6887xq7v0mt3n5
  curl -sS -X POST "$POWERCONTEXT_URL/v1/memory/search" \\
    -H 'content-type: application/json' \\
    -d '{"scope_id":"'"$POWERCONTEXT_SCOPE_ID"'","query":"喜欢吃什么辣的","limit":5}'
`);

const live = serviceConfigFrom({
  POWERCONTEXT_URL: Deno.env.get("POWERCONTEXT_URL"),
  POWERCONTEXT_SCOPE_ID: Deno.env.get("POWERCONTEXT_SCOPE_ID"),
  POWERCONTEXT_API_TOKEN: Deno.env.get("POWERCONTEXT_API_TOKEN"),
  USE_REAL_SERVICES: Deno.env.get("USE_REAL_SERVICES"),
});

if (!live.powerContext) {
  console.log("PowerContext env is unset or forced off. Skipping the live memory probe.");
  console.log("A connected badge requires POST /v1/memory/search to succeed. Health alone is not enough.");
  if (failed > 0) Deno.exit(1);
  Deno.exit(0);
}

const names = new Map(foods.map((food) => [food.id, food.name]));
const client = new PowerContextClient({
  baseUrl: live.powerContext.baseUrl,
  scopeId: live.powerContext.scopeId,
  token: live.powerContext.token,
  foodName: (id) => names.get(id) ?? id,
});

const write = Deno.args.includes("--write");
const userId = "qoder-verify-20261028";
const evidence: Record<string, unknown> = {
  captured_at: new Date().toISOString(),
  powercontext_public_tunnel: live.powerContext.baseUrl,
  tunnel_note: "trycloudflare URLs rotate. Replace POWERCONTEXT_URL when the hostname changes. Do not commit API tokens.",
  scope_id: live.powerContext.scopeId,
  user_id: userId,
  write,
};

if (write) {
  const prefs = {
    favoriteCategories: ["chinese", "hotpot"],
    spicyLevel: 3,
    priceRange: "medium",
    dislikedFoods: ["3"],
    favoriteFoods: ["2", "9"],
  };
  evidence.remember_preferences = await client.setPreferences(userId, prefs);
  evidence.remember_history = await client.addHistory(userId, {
    foodId: "2",
    timestamp: Date.now(),
    liked: true,
  });
  evidence.read_back_preferences = await client.getPreferences(userId);
  evidence.read_back_history = await client.getHistory(userId);
}

evidence.search_query = "喜欢吃什么辣的";
evidence.search_result = await client.searchMemories("喜欢吃什么辣的", 5);
const ping = await client.ping();
evidence.ping = ping;
console.log(JSON.stringify(evidence, null, 2));

const outFlag = Deno.args.indexOf("--out");
if (outFlag >= 0) {
  const outPath = Deno.args[outFlag + 1];
  if (!outPath) {
    console.error("--out requires a file path");
    Deno.exit(2);
  }
  await Deno.writeTextFile(outPath, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(`wrote ${outPath}`);
}

if (ping.hitCount < 1) {
  console.error("PowerContext search returned no hits. The scope may be empty or the tunnel may have rotated.");
  failed += 1;
}

if (failed > 0) Deno.exit(1);
