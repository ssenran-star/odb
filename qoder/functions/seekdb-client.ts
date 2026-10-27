// seekdb 客户端 - 用于菜品数据的语义搜索
// 文档: https://github.com/oceanbase/seekdb-js

export interface SeekDBConfig {
  host?: string;
  port?: number;
  user?: string;
  password?: string;
  database?: string;
  path?: string; // 嵌入式模式
}

export interface FoodDocument {
  id: string;
  name: string;
  category: string;
  tags: string[];
  description: string;
  emoji: string;
  priceRange: string;
  spicy: number;
  healthScore: number;
}

export interface SearchResult {
  id: string;
  document: FoodDocument;
  score: number;
}

// seekdb HTTP API 客户端（服务端模式）
// 实际使用时需要部署 seekdb 服务
export class SeekDBClient {
  private baseUrl: string;
  private collectionName = "foods";
  private initialized = false;

  constructor(config: SeekDBConfig = {}) {
    // 服务端模式: http://host:port/api/v1
    // 嵌入式模式需要通过 Python SDK 或本地代理
    const host = config.host || "127.0.0.1";
    const port = config.port || 2881;
    this.baseUrl = `http://${host}:${port}/api/v1`;
  }

  // 初始化集合（如果不存在则创建）
  async initialize(): Promise<void> {
    if (this.initialized) return;
    
    try {
      // 创建集合，启用自动向量化
      await fetch(`${this.baseUrl}/collections`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: this.collectionName,
          embeddingFunction: {
            name: "default", // 使用默认嵌入模型 all-MiniLM-L6-v2
          },
        }),
      });
      this.initialized = true;
    } catch (error) {
      console.log("seekdb 初始化:", error);
      // 集合可能已存在
      this.initialized = true;
    }
  }

  // 添加菜品数据（自动向量化）
  async addFoods(foods: FoodDocument[]): Promise<void> {
    await this.initialize();

    const documents = foods.map((f) => ({
      id: f.id,
      document: `${f.name} ${f.description} ${f.tags.join(" ")}`,
      metadata: {
        name: f.name,
        category: f.category,
        tags: f.tags,
        description: f.description,
        emoji: f.emoji,
        priceRange: f.priceRange,
        spicy: f.spicy,
        healthScore: f.healthScore,
      },
    }));

    await fetch(`${this.baseUrl}/collections/${this.collectionName}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documents }),
    });
  }

  // 语义搜索
  async search(query: string, filters?: {
    category?: string;
    spicyLevel?: number;
    priceRange?: string;
  }, limit = 10): Promise<SearchResult[]> {
    await this.initialize();

    const where: Record<string, unknown> = {};
    if (filters?.category) where.category = filters.category;
    if (filters?.spicyLevel !== undefined) where.spicy = { $gte: filters.spicyLevel };
    if (filters?.priceRange) where.priceRange = filters.priceRange;

    const response = await fetch(`${this.baseUrl}/collections/${this.collectionName}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        queryTexts: query,
        nResults: limit,
        where: Object.keys(where).length > 0 ? where : undefined,
      }),
    });

    const data = await response.json();
    
    if (!data.results) return [];

    return data.results.map((result: {
      id: string;
      document: string;
      metadata: FoodDocument;
      distance: number;
    }) => ({
      id: result.id,
      document: result.metadata,
      score: 1 - (result.distance || 0), // 转换为相似度分数
    }));
  }

  // 混合搜索（关键词 + 语义）
  async hybridSearch(query: string, keywordFilter?: string, limit = 10): Promise<SearchResult[]> {
    await this.initialize();

    const response = await fetch(`${this.baseUrl}/collections/${this.collectionName}/hybrid-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        queryTexts: query,
        queryText: keywordFilter,
        nResults: limit,
      }),
    });

    const data = await response.json();
    
    if (!data.results) return [];

    return data.results.map((result: {
      id: string;
      document: string;
      metadata: FoodDocument;
      score: number;
    }) => ({
      id: result.id,
      document: result.metadata,
      score: result.score || 0,
    }));
  }

  // 获取所有菜品
  async getAllFoods(): Promise<FoodDocument[]> {
    await this.initialize();

    const response = await fetch(`${this.baseUrl}/collections/${this.collectionName}/get`);
    const data = await response.json();
    
    return data.documents?.map((doc: { metadata: FoodDocument }) => doc.metadata) || [];
  }
}

// 本地模拟客户端（用于演示和测试）
export class SeekDBLocalClient {
  private foods: FoodDocument[] = [];

  constructor(foods: FoodDocument[]) {
    this.foods = foods;
  }

  async addFoods(foods: FoodDocument[]): Promise<void> {
    this.foods.push(...foods);
  }

  async search(query: string, filters?: {
    category?: string;
    spicyLevel?: number;
    priceRange?: string;
  }, limit = 10): Promise<SearchResult[]> {
    const queryLower = query.toLowerCase();
    
    const filtered = this.foods.filter((food) => {
      const matchesQuery = !query || (
        food.name.toLowerCase().includes(queryLower) ||
        food.description.toLowerCase().includes(queryLower) ||
        food.tags.some((tag) => tag.toLowerCase().includes(queryLower)) ||
        food.category.toLowerCase().includes(queryLower)
      );

      const matchesCategory = !filters?.category || food.category === filters.category;
      const matchesSpicy = filters?.spicyLevel === undefined || food.spicy >= filters.spicyLevel;
      const matchesPrice = !filters?.priceRange || food.priceRange === filters.priceRange;

      return matchesQuery && matchesCategory && matchesSpicy && matchesPrice;
    });

    // 模拟相关性评分
    const results: SearchResult[] = filtered.map((food) => ({
      id: food.id,
      document: food,
      score: this.calculateRelevance(food, queryLower),
    }));

    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
  }

  private calculateRelevance(food: FoodDocument, query: string): number {
    if (!query) return 1;
    let score = 0;
    if (food.name.toLowerCase().includes(query)) score += 10;
    if (food.description.toLowerCase().includes(query)) score += 5;
    food.tags.forEach((tag) => {
      if (tag.toLowerCase().includes(query)) score += 3;
    });
    return score;
  }

  async getAllFoods(): Promise<FoodDocument[]> {
    return this.foods;
  }
}
