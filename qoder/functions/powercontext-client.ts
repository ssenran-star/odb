// PowerContext client for meal preferences and eating history.
// Real server: PowerContext 1.4 HTTP API (POST /v1/memory/remember|search|entries/list).
// Docs: https://powercontext.oceanbase.io/en/docs/develop/http-api/

import {
  decodeHistory,
  decodePreferences,
  defaultPreferences,
  encodeHistory,
  encodePreferences,
  type HistoryItem,
  type UserPreferences,
} from "./memory-codec.ts";

export interface PowerContextConfig {
  baseUrl: string;
  scopeId: string;
  token?: string;
  foodName?: (id: string) => string;
}

export interface MemoryRecord {
  kind?: string;
  text?: string;
  state?: string;
}

export interface MemorySearchResult {
  mode: string;
  hits: Array<{ memory?: MemoryRecord; score?: number; matched_by?: string[] }>;
}

export type { HistoryItem, UserPreferences };

export class PowerContextError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "PowerContextError";
    this.status = status;
  }
}

export class PowerContextClient {
  private baseUrl: string;
  private scopeId: string;
  private token?: string;
  private foodName: (id: string) => string;

  constructor(config: PowerContextConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, "");
    this.scopeId = config.scopeId;
    this.token = config.token;
    this.foodName = config.foodName ?? ((id: string) => id);
  }

  async remember(kind: string, text: string): Promise<unknown> {
    const { data } = await this.post("/v1/memory/remember", {
      scope_id: this.scopeId,
      kind,
      text,
    });
    return data;
  }

  async searchMemories(query: string, limit = 10): Promise<MemorySearchResult> {
    const { data } = await this.post("/v1/memory/search", {
      scope_id: this.scopeId,
      query,
      limit,
    });
    const body = data as Partial<MemorySearchResult> | null;
    return {
      mode: typeof body?.mode === "string" ? body.mode : "unknown",
      hits: Array.isArray(body?.hits) ? body.hits : [],
    };
  }

  async listEntries(): Promise<MemoryRecord[]> {
    const records: MemoryRecord[] = [];
    let cursor: string | null = null;
    for (let page = 0; page < 5; page += 1) {
      const body: Record<string, unknown> = { scope_id: this.scopeId, limit: 100 };
      if (cursor) body.cursor = cursor;
      const { data } = await this.post("/v1/memory/entries/list", body);
      const payload = data as { entries?: MemoryRecord[]; next_cursor?: string | null } | null;
      records.push(...(payload?.entries ?? []));
      cursor = payload?.next_cursor ?? null;
      if (!cursor) break;
    }
    return records;
  }

  async ping(): Promise<{ mode: string; hitCount: number }> {
    const result = await this.searchMemories("喜欢吃什么辣的", 5);
    return { mode: result.mode, hitCount: result.hits.length };
  }

  async getPreferences(userId: string): Promise<UserPreferences> {
    const text = await this.latestText(userId, "user_preferences", `用户 ${userId} 偏好`);
    return text ? decodePreferences(text)?.prefs ?? defaultPreferences() : defaultPreferences();
  }

  async setPreferences(userId: string, prefs: UserPreferences): Promise<unknown> {
    return await this.remember(
      "user_preferences",
      encodePreferences(userId, prefs, this.foodName),
    );
  }

  async getHistory(userId: string): Promise<HistoryItem[]> {
    const text = await this.latestText(userId, "eating_history", `用户 ${userId} 最近吃过`);
    return text ? decodeHistory(text)?.items ?? [] : [];
  }

  async addHistory(userId: string, item: HistoryItem): Promise<unknown> {
    const current = await this.getHistory(userId);
    const next = [item, ...current.filter((row) => !(row.foodId === item.foodId && row.timestamp === item.timestamp))];
    return await this.writeHistory(userId, next.slice(0, 20));
  }

  async updateFeedback(userId: string, foodId: string, liked: boolean): Promise<unknown> {
    const history = await this.getHistory(userId);
    const item = history.find((row) => row.foodId === foodId);
    if (item) item.liked = liked;
    else history.unshift({ foodId, timestamp: Date.now(), liked });
    const prefs = await this.getPreferences(userId);
    if (liked) {
      if (!prefs.favoriteFoods.includes(foodId)) prefs.favoriteFoods.push(foodId);
      prefs.dislikedFoods = prefs.dislikedFoods.filter((id) => id !== foodId);
    } else {
      if (!prefs.dislikedFoods.includes(foodId)) prefs.dislikedFoods.push(foodId);
      prefs.favoriteFoods = prefs.favoriteFoods.filter((id) => id !== foodId);
    }
    await this.writeHistory(userId, history.slice(0, 20));
    return await this.setPreferences(userId, prefs);
  }

  async clearHistory(userId: string): Promise<unknown> {
    return await this.writeHistory(userId, []);
  }

  private writeHistory(userId: string, items: HistoryItem[]): Promise<unknown> {
    return this.remember("eating_history", encodeHistory(userId, items, this.foodName));
  }

  private async latestText(userId: string, kind: string, query: string): Promise<string | null> {
    const [searched, listed] = await Promise.all([
      this.searchMemories(query, 20),
      this.listEntries(),
    ]);
    const records: MemoryRecord[] = [
      ...searched.hits.map((hit) => hit.memory ?? {}),
      ...listed,
    ];
    let best: { updatedAt: number; text: string } | null = null;
    for (const record of records) {
      if (!record.text) continue;
      if (record.state && record.state !== "active") continue;
      if (record.kind && record.kind !== kind) continue;
      const decoded = kind === "user_preferences"
        ? decodePreferences(record.text)
        : decodeHistory(record.text);
      if (!decoded || decoded.userId !== userId) continue;
      if (!best || decoded.updatedAt >= best.updatedAt) {
        best = { updatedAt: decoded.updatedAt, text: record.text };
      }
    }
    return best?.text ?? null;
  }

  private async post(path: string, body: Record<string, unknown>): Promise<{ status: number; data: unknown }> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(8000),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "fetch failed";
      throw new PowerContextError(message, 0);
    }

    const raw = await response.text();
    let data: unknown = null;
    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch {
        data = { raw: raw.slice(0, 500) };
      }
    }
    if (!response.ok) {
      const detail = data && typeof data === "object" && "error" in data
        ? JSON.stringify((data as { error: unknown }).error).slice(0, 300)
        : `HTTP ${response.status}`;
      throw new PowerContextError(detail, response.status);
    }
    return { status: response.status, data };
  }
}

export class PowerContextLocalClient {
  private storage = new Map<string, unknown>();

  async getPreferences(userId: string): Promise<UserPreferences> {
    return (this.storage.get(`prefs_${userId}`) as UserPreferences | undefined) ?? defaultPreferences();
  }

  async setPreferences(userId: string, prefs: UserPreferences): Promise<void> {
    this.storage.set(`prefs_${userId}`, prefs);
  }

  async getHistory(userId: string): Promise<HistoryItem[]> {
    return (this.storage.get(`history_${userId}`) as HistoryItem[] | undefined) ?? [];
  }

  async addHistory(userId: string, item: HistoryItem): Promise<void> {
    const history = await this.getHistory(userId);
    history.unshift(item);
    this.storage.set(`history_${userId}`, history.slice(0, 100));
  }

  async updateFeedback(userId: string, foodId: string, liked: boolean): Promise<void> {
    const history = await this.getHistory(userId);
    const item = history.find((row) => row.foodId === foodId);
    if (item) item.liked = liked;
    else history.unshift({ foodId, timestamp: Date.now(), liked });
    this.storage.set(`history_${userId}`, history);

    const prefs = await this.getPreferences(userId);
    if (liked) {
      if (!prefs.favoriteFoods.includes(foodId)) prefs.favoriteFoods.push(foodId);
      prefs.dislikedFoods = prefs.dislikedFoods.filter((id) => id !== foodId);
    } else {
      if (!prefs.dislikedFoods.includes(foodId)) prefs.dislikedFoods.push(foodId);
      prefs.favoriteFoods = prefs.favoriteFoods.filter((id) => id !== foodId);
    }
    await this.setPreferences(userId, prefs);
  }

  async clearHistory(userId: string): Promise<void> {
    this.storage.set(`history_${userId}`, []);
  }
}
