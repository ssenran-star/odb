import { foods, categories, type Food } from "./data.ts";
import { isKnownRoute, normalizeApiPath } from "./routing.mjs";
import { SeekDBClient, SeekDBLocalClient, type FoodDocument, type SearchResult } from "./seekdb-client.ts";
import { PowerContextClient, PowerContextLocalClient, type HistoryItem, type UserPreferences } from "./powercontext-client.ts";
import { SERVICE_ENV_KEYS, serviceConfigFrom, type ServiceConfig } from "./service-config.ts";

const localSeek = new SeekDBLocalClient(foods as FoodDocument[]);
const localPower = new PowerContextLocalClient();

let cachedPower: { key: string; client: PowerContextClient } | null = null;
let cachedSeek: { key: string; client: SeekDBClient } | null = null;

function currentConfig(): ServiceConfig {
  const raw: Record<string, string | undefined> = {};
  for (const key of SERVICE_ENV_KEYS) raw[key] = Deno.env.get(key);
  return serviceConfigFrom(raw);
}

function foodName(id: string): string {
  return foods.find((food) => food.id === id)?.name ?? id;
}

function runtime() {
  const config = currentConfig();
  let power: PowerContextClient | null = null;
  if (config.powerContext) {
    const key = JSON.stringify(config.powerContext);
    if (!cachedPower || cachedPower.key !== key) {
      cachedPower = {
        key,
        client: new PowerContextClient({ ...config.powerContext, foodName }),
      };
    }
    power = cachedPower.client;
  }
  let seek: SeekDBClient | null = null;
  if (config.seekdb) {
    const key = `${config.seekdb.host}:${config.seekdb.port}`;
    if (!cachedSeek || cachedSeek.key !== key) {
      cachedSeek = { key, client: new SeekDBClient(config.seekdb) };
    }
    seek = cachedSeek.client;
  }
  return { config, power, seek };
}

function requestTarget(request: Request): { pathname: string; searchParams: URLSearchParams } {
  try {
    const url = new URL(request.url);
    return { pathname: url.pathname, searchParams: url.searchParams };
  } catch {
    const raw = request.url || "/";
    const query = raw.indexOf("?");
    return {
      pathname: query >= 0 ? raw.slice(0, query) : raw,
      searchParams: new URLSearchParams(query >= 0 ? raw.slice(query + 1) : ""),
    };
  }
}

function resolveRoute(request: Request): { path: string; receivedPath: string; searchParams: URLSearchParams } {
  const { pathname, searchParams } = requestTarget(request);
  let path = normalizeApiPath(pathname);
  if (!isKnownRoute(path)) {
    const forwarded = [
      request.headers.get("x-forwarded-uri"),
      request.headers.get("x-original-uri"),
      request.headers.get("x-forwarded-path"),
      request.headers.get("x-invoke-path"),
    ];
    for (const candidate of forwarded) {
      if (!candidate) continue;
      const normalized = normalizeApiPath(candidate);
      if (isKnownRoute(normalized)) {
        path = normalized;
        break;
      }
    }
  }
  return { path, receivedPath: pathname, searchParams };
}

function jsonResponse(data: unknown, status = 200): Response {
  return Response.json(data, {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}

function errorResponse(message: string, status: number, extra?: Record<string, unknown>): Response {
  return jsonResponse({ ok: false, error: message, ...extra }, status);
}

function getJsonBody(request: Request): Promise<Record<string, unknown>> {
  return request.json().catch(() => ({}));
}

function filtersFrom(searchParams: URLSearchParams): { category?: string; spicyLevel?: number; priceRange?: string } {
  const filters: { category?: string; spicyLevel?: number; priceRange?: string } = {};
  const category = searchParams.get("category");
  const spicyLevel = searchParams.get("spicyLevel");
  const priceRange = searchParams.get("priceRange");
  if (category) filters.category = category;
  if (spicyLevel) filters.spicyLevel = Number.parseInt(spicyLevel, 10);
  if (priceRange) filters.priceRange = priceRange;
  return filters;
}

function userIdFrom(searchParams: URLSearchParams): string {
  return searchParams.get("userId") || "anonymous";
}

async function readPreferences(userId: string): Promise<{ prefs: UserPreferences; source: "powercontext" | "local" }> {
  const { power } = runtime();
  if (power) {
    try {
      return { prefs: await power.getPreferences(userId), source: "powercontext" };
    } catch (error) {
      console.error("PowerContext preferences fallback:", error instanceof Error ? error.message : error);
    }
  }
  return { prefs: await localPower.getPreferences(userId), source: "local" };
}

async function readHistory(userId: string): Promise<{ items: HistoryItem[]; source: "powercontext" | "local" }> {
  const { power } = runtime();
  if (power) {
    try {
      return { items: await power.getHistory(userId), source: "powercontext" };
    } catch (error) {
      console.error("PowerContext history fallback:", error instanceof Error ? error.message : error);
    }
  }
  return { items: await localPower.getHistory(userId), source: "local" };
}

async function searchFoods(
  query: string,
  filters: { category?: string; spicyLevel?: number; priceRange?: string },
): Promise<{ data: FoodDocument[]; searchMethod: "semantic" | "keyword"; source: "seekdb" | "local" }> {
  const { seek } = runtime();
  if (seek && query) {
    try {
      const results = await seek.search(query, filters);
      return {
        data: results.map((result: SearchResult) => result.document),
        searchMethod: "semantic",
        source: "seekdb",
      };
    } catch (error) {
      console.error("seekdb search fallback:", error instanceof Error ? error.message : error);
    }
  }
  const results = await localSeek.search(query, filters);
  return {
    data: results.map((result: SearchResult) => result.document),
    searchMethod: "keyword",
    source: "local",
  };
}

function enrichHistory(items: HistoryItem[]) {
  return items.map((item) => ({
    ...item,
    food: foods.find((food) => food.id === item.foodId),
  }));
}

function shortError(error: unknown): string {
  const message = error instanceof Error ? error.message : "check failed";
  return message.slice(0, 180);
}

export async function handler(request: Request): Promise<Response> {
  const { path, receivedPath, searchParams } = resolveRoute(request);
  const method = request.method.toUpperCase();

  if (method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
      },
    });
  }

  try {
    if ((path === "/" || path === "") && method === "GET") {
      const { config } = runtime();
      return jsonResponse({
        ok: true,
        message: "今天吃什么 API 服务运行中",
        route: "/",
        receivedPath,
        mode: config.powerContext || config.seekdb ? "configured" : "demo",
        services: {
          seekdb: config.seekdb ? "configured" : "unconfigured",
          powerContext: config.powerContext ? "configured" : "unconfigured",
        },
      });
    }

    if (path === "/api/foods" && method === "GET") {
      const results = await localSeek.search("", filtersFrom(searchParams), 100);
      return jsonResponse({
        ok: true,
        data: results.map((result) => result.document),
        source: "catalog",
      });
    }

    if (path === "/api/foods/search" && method === "GET") {
      const query = searchParams.get("q") || "";
      if (!query) return errorResponse("Query parameter 'q' is required", 400, { receivedPath });
      const found = await searchFoods(query, filtersFrom(searchParams));
      return jsonResponse({ ok: true, ...found });
    }

    if (path === "/api/foods/random" && method === "GET") {
      const userId = userIdFrom(searchParams);
      const { prefs, source: prefSource } = await readPreferences(userId);
      const { items: history, source: historySource } = await readHistory(userId);
      const recentIds = history.slice(0, 5).map((item) => item.foodId);
      const available = foods.filter((food) => {
        if (recentIds.includes(food.id)) return false;
        if (prefs.dislikedFoods.includes(food.id)) return false;
        if (prefs.favoriteCategories.length > 0 && !prefs.favoriteCategories.includes(food.category)) return false;
        return true;
      });
      const pool = available.length > 0 ? available : foods.filter((food) => !prefs.dislikedFoods.includes(food.id));
      const usable = pool.length > 0 ? pool : foods;
      const weighted: Food[] = [];
      for (const food of usable) {
        const weight = prefs.favoriteFoods.includes(food.id) ? 3 : 1;
        for (let i = 0; i < weight; i += 1) weighted.push(food);
      }
      const selected = weighted[Math.floor(Math.random() * weighted.length)];
      const memorySource = prefSource === "powercontext" && historySource === "powercontext" ? "powercontext" : "local";
      return jsonResponse({ ok: true, data: selected, memorySource });
    }

    if (path === "/api/categories" && method === "GET") {
      return jsonResponse({ ok: true, data: categories });
    }

    if (path === "/api/user/preferences" && method === "GET") {
      const userId = userIdFrom(searchParams);
      const result = await readPreferences(userId);
      return jsonResponse({ ok: true, data: result.prefs, memorySource: result.source });
    }

    if (path === "/api/user/preferences" && method === "POST") {
      const userId = userIdFrom(searchParams);
      const body = await getJsonBody(request);
      const { power } = runtime();
      const current = await readPreferences(userId);
      const updated: UserPreferences = {
        favoriteCategories: Array.isArray(body.favoriteCategories) ? body.favoriteCategories as string[] : current.prefs.favoriteCategories,
        spicyLevel: typeof body.spicyLevel === "number" ? body.spicyLevel : current.prefs.spicyLevel,
        priceRange: typeof body.priceRange === "string" ? body.priceRange : current.prefs.priceRange,
        dislikedFoods: Array.isArray(body.dislikedFoods) ? body.dislikedFoods as string[] : current.prefs.dislikedFoods,
        favoriteFoods: Array.isArray(body.favoriteFoods) ? body.favoriteFoods as string[] : current.prefs.favoriteFoods,
      };
      if (power) {
        try {
          await power.setPreferences(userId, updated);
          return jsonResponse({ ok: true, data: updated, memorySource: "powercontext" });
        } catch (error) {
          console.error("PowerContext setPreferences fallback:", error instanceof Error ? error.message : error);
        }
      }
      await localPower.setPreferences(userId, updated);
      return jsonResponse({ ok: true, data: updated, memorySource: "local" });
    }

    if (path === "/api/user/history" && method === "GET") {
      const userId = userIdFrom(searchParams);
      const result = await readHistory(userId);
      return jsonResponse({ ok: true, data: enrichHistory(result.items), memorySource: result.source });
    }

    if (path === "/api/user/history" && method === "POST") {
      const userId = userIdFrom(searchParams);
      const body = await getJsonBody(request);
      const foodId = typeof body.foodId === "string" ? body.foodId : "";
      if (!foodId) return errorResponse("foodId is required", 400, { receivedPath });
      const liked = body.liked === true || body.liked === false ? body.liked : null;
      const item: HistoryItem = { foodId, timestamp: Date.now(), liked };
      const { power } = runtime();
      if (power) {
        try {
          await power.addHistory(userId, item);
          return jsonResponse({ ok: true, message: "History updated", memorySource: "powercontext" });
        } catch (error) {
          console.error("PowerContext addHistory fallback:", error instanceof Error ? error.message : error);
        }
      }
      await localPower.addHistory(userId, item);
      return jsonResponse({ ok: true, message: "History updated", memorySource: "local" });
    }

    if (path === "/api/user/history/clear" && method === "POST") {
      const userId = userIdFrom(searchParams);
      const { power } = runtime();
      if (power) {
        try {
          await power.clearHistory(userId);
          return jsonResponse({ ok: true, memorySource: "powercontext" });
        } catch (error) {
          console.error("PowerContext clearHistory fallback:", error instanceof Error ? error.message : error);
        }
      }
      await localPower.clearHistory(userId);
      return jsonResponse({ ok: true, memorySource: "local" });
    }

    if (path === "/api/feedback" && method === "POST") {
      const userId = userIdFrom(searchParams);
      const body = await getJsonBody(request);
      const foodId = typeof body.foodId === "string" ? body.foodId : "";
      if (!foodId || typeof body.liked !== "boolean") {
        return errorResponse("foodId and liked are required", 400, { receivedPath });
      }
      const { power } = runtime();
      if (power) {
        try {
          await power.updateFeedback(userId, foodId, body.liked);
          return jsonResponse({ ok: true, message: "Feedback recorded", memorySource: "powercontext" });
        } catch (error) {
          console.error("PowerContext feedback fallback:", error instanceof Error ? error.message : error);
        }
      }
      await localPower.updateFeedback(userId, foodId, body.liked);
      return jsonResponse({ ok: true, message: "Feedback recorded", memorySource: "local" });
    }

    if (path === "/api/services/status" && method === "GET") {
      const { config, power, seek } = runtime();
      let seekStatus: "connected" | "disconnected" | "unconfigured" = config.seekdb ? "disconnected" : "unconfigured";
      let seekDetail: string | undefined;
      if (seek) {
        try {
          await seek.ping();
          seekStatus = "connected";
        } catch (error) {
          seekStatus = "disconnected";
          seekDetail = shortError(error);
        }
      }

      let powerStatus: "connected" | "disconnected" | "unconfigured" = config.powerContext ? "disconnected" : "unconfigured";
      let powerDetail: string | undefined;
      let searchMode: string | undefined;
      let hitCount: number | undefined;
      if (power) {
        try {
          const ping = await power.ping();
          powerStatus = "connected";
          searchMode = ping.mode;
          hitCount = ping.hitCount;
        } catch (error) {
          powerStatus = "disconnected";
          powerDetail = shortError(error);
        }
      }

      return jsonResponse({
        ok: true,
        route: "/api/services/status",
        receivedPath,
        mode: config.powerContext || config.seekdb ? "configured" : "demo",
        services: {
          seekdb: {
            status: seekStatus,
            configured: Boolean(config.seekdb),
            host: config.seekdb?.host ?? null,
            port: config.seekdb?.port ?? null,
            detail: seekDetail ?? null,
          },
          powerContext: {
            status: powerStatus,
            configured: Boolean(config.powerContext),
            scopeId: config.powerContext?.scopeId ?? null,
            searchMode: searchMode ?? null,
            hitCount: hitCount ?? null,
            detail: powerDetail ?? null,
          },
        },
      });
    }

    if (isKnownRoute(path) && method !== "GET" && method !== "POST") {
      return errorResponse("Method not allowed", 405, { path, receivedPath });
    }

    return errorResponse("Not found", 404, { path, receivedPath });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error("Handler error:", message);
    return errorResponse("Internal server error", 500, { receivedPath });
  }
}
