import { foods, categories, type Food } from "./data.ts";
import { SeekDBClient, SeekDBLocalClient, type FoodDocument, type SearchResult } from "./seekdb-client.ts";
import { PowerContextClient, PowerContextLocalClient, type UserPreferences, type HistoryItem } from "./powercontext-client.ts";

// 配置：设置为 true 使用真实的 seekdb/PowerContext 服务
// 设置为 false 使用本地模拟（演示模式）
const USE_REAL_SERVICES = false;

// seekdb 配置
const SEEKDB_CONFIG = {
  host: Deno.env.get("SEEKDB_HOST") || "127.0.0.1",
  port: parseInt(Deno.env.get("SEEKDB_PORT") || "2881"),
  user: Deno.env.get("SEEKDB_USER") || "root",
  password: Deno.env.get("SEEKDB_PASSWORD") || "",
  database: Deno.env.get("SEEKDB_DATABASE") || "food_app",
};

// PowerContext 配置
const POWERCONTEXT_CONFIG = {
  baseUrl: Deno.env.get("POWERCONTEXT_URL") || "http://127.0.0.1:8000",
  scope: Deno.env.get("POWERCONTEXT_SCOPE") || "what-to-eat",
};

// 初始化客户端
let seekdb: SeekDBClient | SeekDBLocalClient;
let powerContext: PowerContextClient | PowerContextLocalClient;

if (USE_REAL_SERVICES) {
  seekdb = new SeekDBClient(SEEKDB_CONFIG);
  powerContext = new PowerContextClient(POWERCONTEXT_CONFIG);
  
  // 初始化 seekdb 数据
  (async () => {
    try {
      const foodDocs: FoodDocument[] = foods.map((f) => ({
        id: f.id,
        name: f.name,
        category: f.category,
        tags: f.tags,
        description: f.description,
        emoji: f.emoji,
        priceRange: f.priceRange,
        spicy: f.spicy,
        healthScore: f.healthScore,
      }));
      await seekdb.addFoods(foodDocs);
      console.log("seekdb 数据初始化完成");
    } catch (error) {
      console.error("seekdb 初始化失败:", error);
    }
  })();
} else {
  seekdb = new SeekDBLocalClient(foods as FoodDocument[]);
  powerContext = new PowerContextLocalClient();
}

function getJsonBody(request: Request): Promise<Record<string, unknown>> {
  return request.json().catch(() => ({}));
}

function getUserId(request: Request): string {
  const url = new URL(request.url);
  return url.searchParams.get("userId") || "anonymous";
}

function jsonResponse(data: unknown, status = 200): Response {
  return Response.json(data, {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function errorResponse(message: string, status: number): Response {
  return jsonResponse({ ok: false, error: message }, status);
}

export async function handler(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/functions\/v1\/app/, "");
  const method = request.method;

  try {
    // 健康检查
    if (path === "" || path === "/") {
      return jsonResponse({ 
        ok: true, 
        message: "今天吃什么 API 服务运行中",
        mode: USE_REAL_SERVICES ? "production" : "demo",
        services: {
          seekdb: USE_REAL_SERVICES ? SEEKDB_CONFIG.host : "local",
          powerContext: USE_REAL_SERVICES ? POWERCONTEXT_CONFIG.baseUrl : "local",
        },
      });
    }

    // GET /api/foods - 获取所有菜品（支持筛选）
    if (path === "/api/foods" && method === "GET") {
      const category = url.searchParams.get("category");
      const spicyLevel = url.searchParams.get("spicyLevel");
      const priceRange = url.searchParams.get("priceRange");

      const filters: { category?: string; spicyLevel?: number; priceRange?: string } = {};
      if (category) filters.category = category;
      if (spicyLevel) filters.spicyLevel = parseInt(spicyLevel);
      if (priceRange) filters.priceRange = priceRange;

      const results = await seekdb.search("", filters);
      return jsonResponse({ ok: true, data: results.map((r: SearchResult) => r.document) });
    }

    // GET /api/foods/search - seekdb 语义搜索
    if (path === "/api/foods/search" && method === "GET") {
      const query = url.searchParams.get("q") || "";
      const category = url.searchParams.get("category");
      const spicyLevel = url.searchParams.get("spicyLevel");
      const priceRange = url.searchParams.get("priceRange");

      if (!query) {
        return errorResponse("Query parameter 'q' is required", 400);
      }

      const filters: { category?: string; spicyLevel?: number; priceRange?: string } = {};
      if (category) filters.category = category;
      if (spicyLevel) filters.spicyLevel = parseInt(spicyLevel);
      if (priceRange) filters.priceRange = priceRange;

      // 使用 seekdb 进行语义搜索
      const results = await seekdb.search(query, filters);
      return jsonResponse({ 
        ok: true, 
        data: results.map((r: SearchResult) => r.document),
        searchMethod: USE_REAL_SERVICES ? "semantic" : "keyword",
      });
    }

    // GET /api/foods/random - 智能推荐（结合 PowerContext 用户偏好）
    if (path === "/api/foods/random" && method === "GET") {
      const userId = getUserId(request);
      
      // 从 PowerContext 获取用户偏好和历史
      const prefs = await powerContext.getPreferences(userId);
      const history = await powerContext.getHistory(userId);

      const recentIds = history.slice(0, 5).map((h) => h.foodId);
      
      // 筛选可用菜品
      const available = foods.filter((f) => {
        // 排除最近吃过的
        if (recentIds.includes(f.id)) return false;
        // 排除不喜欢的
        if (prefs.dislikedFoods.includes(f.id)) return false;
        // 如果有偏好菜系，优先匹配
        if (prefs.favoriteCategories.length > 0 && !prefs.favoriteCategories.includes(f.category)) {
          return false;
        }
        return true;
      });

      const pool = available.length > 0 ? available : foods;
      
      // 如果用户有喜欢的菜品，增加权重
      const weightedPool: Food[] = [];
      pool.forEach((f) => {
        const weight = prefs.favoriteFoods.includes(f.id) ? 3 : 1;
        for (let i = 0; i < weight; i++) {
          weightedPool.push(f);
        }
      });

      const selected = weightedPool[Math.floor(Math.random() * weightedPool.length)];
      return jsonResponse({ ok: true, data: selected });
    }

    // GET /api/categories - 获取所有分类
    if (path === "/api/categories" && method === "GET") {
      return jsonResponse({ ok: true, data: categories });
    }

    // GET /api/user/preferences - 获取用户偏好（PowerContext）
    if (path === "/api/user/preferences" && method === "GET") {
      const userId = getUserId(request);
      const prefs = await powerContext.getPreferences(userId);
      return jsonResponse({ ok: true, data: prefs });
    }

    // POST /api/user/preferences - 更新用户偏好（PowerContext）
    if (path === "/api/user/preferences" && method === "POST") {
      const userId = getUserId(request);
      const body = await getJsonBody(request);
      const current = await powerContext.getPreferences(userId);
      const updated = { ...current, ...body };
      await powerContext.setPreferences(userId, updated);
      return jsonResponse({ ok: true, data: updated });
    }

    // GET /api/user/history - 获取用餐历史（PowerContext）
    if (path === "/api/user/history" && method === "GET") {
      const userId = getUserId(request);
      const history = await powerContext.getHistory(userId);
      const enriched = history.map((item) => ({
        ...item,
        food: foods.find((f) => f.id === item.foodId),
      }));
      return jsonResponse({ ok: true, data: enriched });
    }

    // POST /api/user/history - 添加用餐记录（PowerContext）
    if (path === "/api/user/history" && method === "POST") {
      const userId = getUserId(request);
      const body = await getJsonBody(request);
      const { foodId, liked } = body as { foodId: string; liked: boolean | null };

      if (!foodId) {
        return errorResponse("foodId is required", 400);
      }

      await powerContext.addHistory(userId, {
        foodId,
        timestamp: Date.now(),
        liked: liked ?? null,
      });

      return jsonResponse({ ok: true, message: "History updated" });
    }

    // POST /api/feedback - 记录反馈（PowerContext）
    if (path === "/api/feedback" && method === "POST") {
      const userId = getUserId(request);
      const body = await getJsonBody(request);
      const { foodId, liked } = body as { foodId: string; liked: boolean };

      if (!foodId || liked === undefined) {
        return errorResponse("foodId and liked are required", 400);
      }

      await powerContext.updateFeedback(userId, foodId, liked);
      return jsonResponse({ ok: true, message: "Feedback recorded" });
    }

    // GET /api/services/status - 检查服务状态
    if (path === "/api/services/status" && method === "GET") {
      let seekdbStatus = "unknown";
      let powerContextStatus = "unknown";

      if (USE_REAL_SERVICES) {
        try {
          await seekdb.getAllFoods();
          seekdbStatus = "connected";
        } catch {
          seekdbStatus = "disconnected";
        }

        try {
          await powerContext.getPreferences("test");
          powerContextStatus = "connected";
        } catch {
          powerContextStatus = "disconnected";
        }
      } else {
        seekdbStatus = "demo";
        powerContextStatus = "demo";
      }

      return jsonResponse({
        ok: true,
        mode: USE_REAL_SERVICES ? "production" : "demo",
        services: {
          seekdb: {
            status: seekdbStatus,
            config: USE_REAL_SERVICES ? { host: SEEKDB_CONFIG.host, port: SEEKDB_CONFIG.port } : null,
          },
          powerContext: {
            status: powerContextStatus,
            config: USE_REAL_SERVICES ? { baseUrl: POWERCONTEXT_CONFIG.baseUrl } : null,
          },
        },
      });
    }

    return errorResponse("Not found", 404);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("Handler error:", message);
    return errorResponse("Internal server error", 500);
  }
}
