// Encode preferences and history as searchable Chinese text plus one JSON line.
// PowerContext 1.4 stores memories as text via POST /v1/memory/remember.

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

export interface StoredPreferences {
  userId: string;
  updatedAt: number;
  prefs: UserPreferences;
}

export interface StoredHistory {
  userId: string;
  updatedAt: number;
  items: HistoryItem[];
}

const MARKER = "\nPCJSON:";

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function likedWord(liked: boolean | null): string {
  if (liked === true) return "喜欢";
  if (liked === false) return "不喜欢";
  return "未评价";
}

export function encodePreferences(
  userId: string,
  prefs: UserPreferences,
  foodName: (id: string) => string,
  now = Date.now(),
): string {
  const categories = prefs.favoriteCategories.length > 0 ? prefs.favoriteCategories.join("、") : "不限";
  const liked = prefs.favoriteFoods.map(foodName).filter(Boolean).join("、") || "无";
  const disliked = prefs.dislikedFoods.map(foodName).filter(Boolean).join("、") || "无";
  const summary = `用户 ${userId} 偏好：喜欢的菜系 ${categories}；辣度偏好 ${prefs.spicyLevel}；价位 ${prefs.priceRange}；喜欢的菜 ${liked}；不喜欢 ${disliked}。`;
  const payload = {
    v: 1,
    kind: "user_preferences",
    userId,
    updatedAt: now,
    favoriteCategories: prefs.favoriteCategories,
    spicyLevel: prefs.spicyLevel,
    priceRange: prefs.priceRange,
    dislikedFoods: prefs.dislikedFoods,
    favoriteFoods: prefs.favoriteFoods,
  };
  return `${summary}${MARKER}${JSON.stringify(payload)}`;
}

export function decodePreferences(text: string): StoredPreferences | null {
  const index = text.lastIndexOf(MARKER);
  if (index < 0) return null;
  try {
    const payload = JSON.parse(text.slice(index + MARKER.length)) as Record<string, unknown>;
    if (payload.v !== 1 || payload.kind !== "user_preferences") return null;
    if (typeof payload.userId !== "string" || typeof payload.updatedAt !== "number") return null;
    const spicy = Number(payload.spicyLevel);
    return {
      userId: payload.userId,
      updatedAt: payload.updatedAt,
      prefs: {
        favoriteCategories: asStringArray(payload.favoriteCategories),
        spicyLevel: Number.isFinite(spicy) ? spicy : 0,
        priceRange: typeof payload.priceRange === "string" ? payload.priceRange : "medium",
        dislikedFoods: asStringArray(payload.dislikedFoods),
        favoriteFoods: asStringArray(payload.favoriteFoods),
      },
    };
  } catch {
    return null;
  }
}

export function encodeHistory(
  userId: string,
  items: HistoryItem[],
  foodName: (id: string) => string,
  now = Date.now(),
): string {
  const recent = items.slice(0, 20);
  const summaryBits = recent.slice(0, 8).map((item) => {
    return `${foodName(item.foodId)} ${item.foodId}（${likedWord(item.liked)}）`;
  });
  const summary = summaryBits.length > 0
    ? `用户 ${userId} 最近吃过：${summaryBits.join("、")}。时间戳用于避免重复推荐。`
    : `用户 ${userId} 最近吃过：无。时间戳用于避免重复推荐。`;
  const payload = {
    v: 1,
    kind: "eating_history",
    userId,
    updatedAt: now,
    items: recent,
  };
  return `${summary}${MARKER}${JSON.stringify(payload)}`;
}

export function decodeHistory(text: string): StoredHistory | null {
  const index = text.lastIndexOf(MARKER);
  if (index < 0) return null;
  try {
    const payload = JSON.parse(text.slice(index + MARKER.length)) as Record<string, unknown>;
    if (payload.v !== 1 || payload.kind !== "eating_history") return null;
    if (typeof payload.userId !== "string" || typeof payload.updatedAt !== "number") return null;
    const items = Array.isArray(payload.items)
      ? payload.items.flatMap((item) => {
        if (!item || typeof item !== "object") return [];
        const row = item as Record<string, unknown>;
        if (typeof row.foodId !== "string" || typeof row.timestamp !== "number") return [];
        const liked = row.liked === true || row.liked === false ? row.liked : null;
        return [{ foodId: row.foodId, timestamp: row.timestamp, liked }];
      })
      : [];
    return { userId: payload.userId, updatedAt: payload.updatedAt, items };
  } catch {
    return null;
  }
}

export function defaultPreferences(): UserPreferences {
  return {
    favoriteCategories: [],
    spicyLevel: 0,
    priceRange: "medium",
    dislikedFoods: [],
    favoriteFoods: [],
  };
}
