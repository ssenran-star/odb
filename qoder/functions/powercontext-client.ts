// PowerContext 客户端 - 用于用户记忆和上下文管理
// 文档: https://github.com/oceanbase/powercontext

export interface PowerContextConfig {
  baseUrl?: string;
  scope?: string; // 项目/用户范围
}

export interface Memory {
  id: string;
  content: string;
  scope: string;
  source?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}

export interface Handoff {
  id: string;
  scope: string;
  status: "pending" | "accepted" | "completed";
  context: Record<string, unknown>;
  created_at: string;
  accepted_at?: string;
}

export interface UserPreferences {
  favoriteCategories: string[];
  spicyLevel: number;
  priceRange: string;
  dislikedFoods: string[];
  favoriteFoods: string[];
}

export interface HistoryItem {
  foodId: string;
  timestamp: number;
  liked: boolean | null;
}

// PowerContext HTTP API 客户端
// PowerContext Server 默认监听 http://127.0.0.1:8000
export class PowerContextClient {
  private baseUrl: string;
  private scope: string;

  constructor(config: PowerContextConfig = {}) {
    this.baseUrl = config.baseUrl || "http://127.0.0.1:8000";
    this.scope = config.scope || "default";
  }

  // 创建或更新 Memory（用户偏好）
  async setMemory(key: string, content: unknown, metadata?: Record<string, unknown>): Promise<Memory> {
    const response = await fetch(`${this.baseUrl}/v1/memories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scope: this.scope,
        key,
        content: JSON.stringify(content),
        metadata: {
          type: "user_preference",
          ...metadata,
        },
      }),
    });
    return response.json();
  }

  // 获取 Memory
  async getMemory<T>(key: string): Promise<T | null> {
    try {
      const response = await fetch(
        `${this.baseUrl}/v1/memories?scope=${encodeURIComponent(this.scope)}&key=${encodeURIComponent(key)}`
      );
      const data = await response.json();
      
      if (!data.memories || data.memories.length === 0) return null;
      
      const content = data.memories[0].content;
      return JSON.parse(content) as T;
    } catch {
      return null;
    }
  }

  // 搜索 Memories（语义搜索）
  async searchMemories(query: string, limit = 10): Promise<Memory[]> {
    const response = await fetch(`${this.baseUrl}/v1/memories/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scope: this.scope,
        query,
        limit,
      }),
    });
    const data = await response.json();
    return data.memories || [];
  }

  // 删除 Memory
  async deleteMemory(key: string): Promise<void> {
    await fetch(`${this.baseUrl}/v1/memories/${encodeURIComponent(key)}?scope=${encodeURIComponent(this.scope)}`, {
      method: "DELETE",
    });
  }

  // 创建 Handoff（任务交接）
  async createHandoff(context: Record<string, unknown>): Promise<Handoff> {
    const response = await fetch(`${this.baseUrl}/v1/handoffs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scope: this.scope,
        context,
      }),
    });
    return response.json();
  }

  // 获取当前 Handoff
  async getHandoff(): Promise<Handoff | null> {
    try {
      const response = await fetch(
        `${this.baseUrl}/v1/handoffs?scope=${encodeURIComponent(this.scope)}&status=pending`
      );
      const data = await response.json();
      
      if (!data.handoffs || data.handoffs.length === 0) return null;
      return data.handoffs[0];
    } catch {
      return null;
    }
  }

  // 接受 Handoff
  async acceptHandoff(handoffId: string): Promise<void> {
    await fetch(`${this.baseUrl}/v1/handoffs/${handoffId}/accept`, {
      method: "POST",
    });
  }

  // 用户偏好相关方法
  async getPreferences(userId: string): Promise<UserPreferences> {
    const prefs = await this.getMemory<UserPreferences>(`prefs_${userId}`);
    return prefs || {
      favoriteCategories: [],
      spicyLevel: 0,
      priceRange: "medium",
      dislikedFoods: [],
      favoriteFoods: [],
    };
  }

  async setPreferences(userId: string, prefs: UserPreferences): Promise<void> {
    await this.setMemory(`prefs_${userId}`, prefs, { type: "user_preferences" });
  }

  async getHistory(userId: string): Promise<HistoryItem[]> {
    const history = await this.getMemory<HistoryItem[]>(`history_${userId}`);
    return history || [];
  }

  async addHistory(userId: string, item: HistoryItem): Promise<void> {
    const history = await this.getHistory(userId);
    history.unshift(item);
    // 只保留最近 100 条
    await this.setMemory(`history_${userId}`, history.slice(0, 100), { type: "eating_history" });
  }

  async updateFeedback(userId: string, foodId: string, liked: boolean): Promise<void> {
    const history = await this.getHistory(userId);
    const item = history.find((h) => h.foodId === foodId);
    if (item) {
      item.liked = liked;
      await this.setMemory(`history_${userId}`, history, { type: "eating_history" });
    }

    // 更新偏好
    const prefs = await this.getPreferences(userId);
    if (liked) {
      if (!prefs.favoriteFoods.includes(foodId)) {
        prefs.favoriteFoods.push(foodId);
      }
    } else {
      if (!prefs.dislikedFoods.includes(foodId)) {
        prefs.dislikedFoods.push(foodId);
      }
    }
    await this.setPreferences(userId, prefs);
  }
}

// 本地模拟客户端（用于演示和测试）
export class PowerContextLocalClient {
  private storage = new Map<string, unknown>();

  async getPreferences(userId: string): Promise<UserPreferences> {
    const key = `prefs_${userId}`;
    return (this.storage.get(key) as UserPreferences) || {
      favoriteCategories: [],
      spicyLevel: 0,
      priceRange: "medium",
      dislikedFoods: [],
      favoriteFoods: [],
    };
  }

  async setPreferences(userId: string, prefs: UserPreferences): Promise<void> {
    this.storage.set(`prefs_${userId}`, prefs);
  }

  async getHistory(userId: string): Promise<HistoryItem[]> {
    const key = `history_${userId}`;
    return (this.storage.get(key) as HistoryItem[]) || [];
  }

  async addHistory(userId: string, item: HistoryItem): Promise<void> {
    const key = `history_${userId}`;
    const history = await this.getHistory(userId);
    history.unshift(item);
    this.storage.set(key, history.slice(0, 100));
  }

  async updateFeedback(userId: string, foodId: string, liked: boolean): Promise<void> {
    const key = `history_${userId}`;
    const history = await this.getHistory(userId);
    const item = history.find((h) => h.foodId === foodId);
    if (item) {
      item.liked = liked;
      this.storage.set(key, history);
    }

    const prefs = await this.getPreferences(userId);
    if (liked) {
      if (!prefs.favoriteFoods.includes(foodId)) {
        prefs.favoriteFoods.push(foodId);
      }
    } else {
      if (!prefs.dislikedFoods.includes(foodId)) {
        prefs.dislikedFoods.push(foodId);
      }
    }
    await this.setPreferences(userId, prefs);
  }
}
