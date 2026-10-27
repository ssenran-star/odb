export interface Food {
  id: string;
  name: string;
  category: string;
  tags: string[];
  description: string;
  emoji: string;
  priceRange: "low" | "medium" | "high";
  spicy: number;
  healthScore: number;
}

export const categories = [
  { id: "chinese", name: "中餐", emoji: "🥢" },
  { id: "western", name: "西餐", emoji: "🍝" },
  { id: "japanese", name: "日料", emoji: "🍣" },
  { id: "fast", name: "快餐", emoji: "🍔" },
  { id: "noodle", name: "面食", emoji: "🍜" },
  { id: "hotpot", name: "火锅", emoji: "🍲" },
  { id: "bbq", name: "烧烤", emoji: "🍖" },
  { id: "dessert", name: "甜品", emoji: "🍰" },
];

export const foods: Food[] = [
  { id: "1", name: "红烧牛肉面", category: "noodle", tags: ["牛肉", "面条", "红烧"], description: "浓郁汤底，劲道面条", emoji: "🍜", priceRange: "low", spicy: 1, healthScore: 7 },
  { id: "2", name: "麻辣火锅", category: "hotpot", tags: ["麻辣", "涮菜", "聚餐"], description: "地道川味，鲜香麻辣", emoji: "🍲", priceRange: "high", spicy: 3, healthScore: 4 },
  { id: "3", name: "寿司拼盘", category: "japanese", tags: ["生鲜", "米饭", "清淡"], description: "新鲜食材，精致摆盘", emoji: "🍣", priceRange: "high", spicy: 0, healthScore: 9 },
  { id: "4", name: "宫保鸡丁", category: "chinese", tags: ["鸡肉", "花生", "微辣"], description: "经典川菜，下饭神器", emoji: "🍗", priceRange: "medium", spicy: 2, healthScore: 6 },
  { id: "5", name: "意大利面", category: "western", tags: ["番茄", "肉酱", "芝士"], description: "浓郁肉酱，弹牙面条", emoji: "🍝", priceRange: "medium", spicy: 0, healthScore: 6 },
  { id: "6", name: "汉堡薯条", category: "fast", tags: ["牛肉", "炸鸡", "快餐"], description: "经典搭配，快速满足", emoji: "🍔", priceRange: "low", spicy: 0, healthScore: 3 },
  { id: "7", name: "烤羊肉串", category: "bbq", tags: ["羊肉", "烤制", "夜宵"], description: "炭火烤制，香气四溢", emoji: "🍖", priceRange: "medium", spicy: 2, healthScore: 4 },
  { id: "8", name: "提拉米苏", category: "dessert", tags: ["咖啡", "芝士", "甜品"], description: "层次丰富，甜而不腻", emoji: "🍰", priceRange: "medium", spicy: 0, healthScore: 3 },
  { id: "9", name: "酸菜鱼", category: "chinese", tags: ["鱼肉", "酸菜", "麻辣"], description: "鲜嫩鱼片，酸爽开胃", emoji: "🐟", priceRange: "medium", spicy: 2, healthScore: 7 },
  { id: "10", name: "日式拉面", category: "japanese", tags: ["猪骨", "叉烧", "溏心蛋"], description: "浓厚汤底，弹牙面条", emoji: "🍜", priceRange: "medium", spicy: 0, healthScore: 6 },
  { id: "11", name: "披萨", category: "western", tags: ["芝士", "番茄", "烤制"], description: "拉丝芝士，丰富配料", emoji: "🍕", priceRange: "medium", spicy: 0, healthScore: 4 },
  { id: "12", name: "麻辣烫", category: "hotpot", tags: ["自选", "麻辣", "快餐"], description: "自由搭配，麻辣鲜香", emoji: "🥘", priceRange: "low", spicy: 2, healthScore: 5 },
  { id: "13", name: "饺子", category: "chinese", tags: ["面食", "馅料", "传统"], description: "皮薄馅大，蘸醋更香", emoji: "🥟", priceRange: "low", spicy: 0, healthScore: 7 },
  { id: "14", name: "炸鸡", category: "fast", tags: ["鸡肉", "油炸", "快餐"], description: "外酥里嫩，搭配酱料", emoji: "🍗", priceRange: "low", spicy: 1, healthScore: 3 },
  { id: "15", name: "抹茶蛋糕", category: "dessert", tags: ["抹茶", "奶油", "甜品"], description: "清新抹茶，绵密口感", emoji: "🍵", priceRange: "medium", spicy: 0, healthScore: 3 },
  { id: "16", name: "烤鸭", category: "chinese", tags: ["鸭肉", "烤制", "北京"], description: "皮脆肉嫩，蘸酱卷饼", emoji: "🦆", priceRange: "high", spicy: 0, healthScore: 6 },
  { id: "17", name: "螺蛳粉", category: "noodle", tags: ["米粉", "酸辣", "广西"], description: "酸辣鲜香，独特风味", emoji: "🍜", priceRange: "low", spicy: 3, healthScore: 5 },
  { id: "18", name: "牛排", category: "western", tags: ["牛肉", "煎烤", "西餐"], description: "鲜嫩多汁，搭配红酒", emoji: "🥩", priceRange: "high", spicy: 0, healthScore: 7 },
  { id: "19", name: "章鱼小丸子", category: "japanese", tags: ["章鱼", "小吃", "日式"], description: "外酥内软，酱汁浓郁", emoji: "🐙", priceRange: "low", spicy: 0, healthScore: 4 },
  { id: "20", name: "烤串拼盘", category: "bbq", tags: ["混合", "烤制", "聚餐"], description: "多种烤串，畅享美味", emoji: "🍢", priceRange: "medium", spicy: 2, healthScore: 4 },
];
