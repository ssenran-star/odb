import type { Food } from "../data/foods";

const API_BASE = "/functions/v1/app";

async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
  message?: string;
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
  food?: Food;
}

export const api = {
  async getFoods(filters?: { category?: string; spicyLevel?: number; priceRange?: string }): Promise<Food[]> {
    const params = new URLSearchParams();
    if (filters?.category) params.set("category", filters.category);
    if (filters?.spicyLevel !== undefined) params.set("spicyLevel", String(filters.spicyLevel));
    if (filters?.priceRange) params.set("priceRange", filters.priceRange);
    const result = await requestJson<ApiResponse<Food[]>>(`${API_BASE}/api/foods?${params}`);
    return result.data || [];
  },

  async searchFoods(query: string, filters?: { category?: string; spicyLevel?: number; priceRange?: string }): Promise<Food[]> {
    const params = new URLSearchParams({ q: query });
    if (filters?.category) params.set("category", filters.category);
    if (filters?.spicyLevel !== undefined) params.set("spicyLevel", String(filters.spicyLevel));
    if (filters?.priceRange) params.set("priceRange", filters.priceRange);
    const result = await requestJson<ApiResponse<Food[]>>(`${API_BASE}/api/foods/search?${params}`);
    return result.data || [];
  },

  async getRandomFood(userId?: string): Promise<Food> {
    const params = userId ? `?userId=${userId}` : "";
    const result = await requestJson<ApiResponse<Food>>(`${API_BASE}/api/foods/random${params}`);
    if (!result.data) throw new Error("No food returned");
    return result.data;
  },

  async getPreferences(userId?: string): Promise<UserPreferences> {
    const params = userId ? `?userId=${userId}` : "";
    const result = await requestJson<ApiResponse<UserPreferences>>(`${API_BASE}/api/user/preferences${params}`);
    return result.data || { favoriteCategories: [], spicyLevel: 0, priceRange: "medium", dislikedFoods: [], favoriteFoods: [] };
  },

  async updatePreferences(prefs: Partial<UserPreferences>, userId?: string): Promise<UserPreferences> {
    const params = userId ? `?userId=${userId}` : "";
    const result = await requestJson<ApiResponse<UserPreferences>>(`${API_BASE}/api/user/preferences${params}`, {
      method: "POST",
      body: JSON.stringify(prefs),
    });
    return result.data || prefs as UserPreferences;
  },

  async getHistory(userId?: string): Promise<HistoryItem[]> {
    const params = userId ? `?userId=${userId}` : "";
    const result = await requestJson<ApiResponse<HistoryItem[]>>(`${API_BASE}/api/user/history${params}`);
    return result.data || [];
  },

  async addHistory(foodId: string, liked: boolean | null, userId?: string): Promise<void> {
    const params = userId ? `?userId=${userId}` : "";
    await requestJson<ApiResponse<unknown>>(`${API_BASE}/api/user/history${params}`, {
      method: "POST",
      body: JSON.stringify({ foodId, liked }),
    });
  },

  async recordFeedback(foodId: string, liked: boolean, userId?: string): Promise<void> {
    const params = userId ? `?userId=${userId}` : "";
    await requestJson<ApiResponse<unknown>>(`${API_BASE}/api/feedback${params}`, {
      method: "POST",
      body: JSON.stringify({ foodId, liked }),
    });
  },
};
