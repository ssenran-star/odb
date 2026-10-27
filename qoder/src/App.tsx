import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { foods, categories, type Food } from "./data/foods";
import { SpinWheel } from "./components/SpinWheel";
import { FoodCard } from "./components/FoodCard";
import { HistoryPanel } from "./components/HistoryPanel";
import { FilterPanel } from "./components/FilterPanel";
import { SearchResults } from "./components/SearchResults";
import { api, type HistoryItem } from "./lib/api";

const USER_ID = "user_" + (localStorage.getItem("userId") || (() => {
  const id = Math.random().toString(36).slice(2);
  localStorage.setItem("userId", id);
  return id;
})());

export default function App() {
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [isSpinning, setIsSpinning] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [spicyLevel, setSpicyLevel] = useState<number | null>(null);
  const [priceRange, setPriceRange] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Food[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [useBackend, setUseBackend] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await api.getHistory(USER_ID);
      setHistory(data);
    } catch {
      const saved = localStorage.getItem("food-history");
      if (saved) {
        try { setHistory(JSON.parse(saved)); } catch { /* ignore */ }
      }
    }
  };

  const saveHistory = (items: HistoryItem[]) => {
    localStorage.setItem("food-history", JSON.stringify(items));
  };

  const getFilteredFoods = useCallback(() => {
    return foods.filter((food) => {
      if (selectedCategories.length > 0 && !selectedCategories.includes(food.category)) return false;
      if (spicyLevel !== null && food.spicy < spicyLevel) return false;
      if (priceRange && food.priceRange !== priceRange) return false;
      const recentIds = history.slice(0, 5).map((h) => h.foodId || h.food?.id);
      if (recentIds.includes(food.id)) return false;
      return true;
    });
  }, [selectedCategories, spicyLevel, priceRange, history]);

  const handleSpin = async () => {
    setIsSpinning(true);
    try {
      if (useBackend) {
        const food = await api.getRandomFood(USER_ID);
        setSelectedFood(food);
      } else {
        const filtered = getFilteredFoods();
        const pool = filtered.length > 0 ? filtered : foods;
        setSelectedFood(pool[Math.floor(Math.random() * pool.length)]);
      }
    } catch {
      const filtered = getFilteredFoods();
      const pool = filtered.length > 0 ? filtered : foods;
      setSelectedFood(pool[Math.floor(Math.random() * pool.length)]);
    }
  };

  const handleSpinEnd = async () => {
    setIsSpinning(false);
    if (selectedFood) {
      const newItem: HistoryItem = {
        foodId: selectedFood.id,
        timestamp: Date.now(),
        liked: null,
        food: selectedFood,
      };
      const newHistory = [newItem, ...history.slice(0, 49)];
      setHistory(newHistory);
      saveHistory(newHistory);

      try {
        await api.addHistory(selectedFood.id, null, USER_ID);
      } catch { /* fallback to local storage */ }
    }
  };

  const handleFeedback = async (liked: boolean) => {
    if (!selectedFood) return;

    const newHistory = history.map((item, idx) =>
      idx === 0 ? { ...item, liked } : item
    );
    setHistory(newHistory);
    saveHistory(newHistory);

    try {
      await api.recordFeedback(selectedFood.id, liked, USER_ID);
    } catch { /* fallback to local storage */ }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await api.searchFoods(searchQuery, {
        category: selectedCategories[0],
        spicyLevel: spicyLevel ?? undefined,
        priceRange: priceRange ?? undefined,
      });
      setSearchResults(results);
    } catch {
      const query = searchQuery.toLowerCase();
      const results = foods.filter((f) =>
        f.name.toLowerCase().includes(query) ||
        f.tags.some((t) => t.toLowerCase().includes(query)) ||
        f.description.toLowerCase().includes(query)
      );
      setSearchResults(results);
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearHistory = async () => {
    setHistory([]);
    localStorage.removeItem("food-history");
  };

  return (
    <main className="mx-auto min-h-dvh max-w-4xl p-4 md:p-8">
      <div className="mb-8 text-center">
        <h1 className="mb-2 text-4xl font-bold tracking-tight md:text-5xl">
          🍽️ 今天吃什么
        </h1>
        <p className="text-muted-foreground">选择困难症终结者，转一转就知道</p>
        <div className="mt-3 flex justify-center gap-2">
          <Button
            variant={useBackend ? "default" : "outline"}
            size="sm"
            onClick={() => setUseBackend(true)}
          >
            🌐 在线模式
          </Button>
          <Button
            variant={!useBackend ? "default" : "outline"}
            size="sm"
            onClick={() => setUseBackend(false)}
          >
            💾 本地模式
          </Button>
        </div>
      </div>

      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <Input
              placeholder="搜索：想吃辣的、清淡的、便宜的..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={isSearching}>
              {isSearching ? "搜索中..." : "🔍 搜索"}
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {useBackend ? "使用 seekdb 语义搜索" : "本地关键词搜索"}
          </p>
        </CardContent>
      </Card>

      {searchResults.length > 0 && (
        <SearchResults
          results={searchResults}
          onSelect={(food) => {
            setSelectedFood(food);
            setSearchResults([]);
            setSearchQuery("");
          }}
          onClose={() => setSearchResults([])}
        />
      )}

      <FilterPanel
        categories={categories}
        selectedCategories={selectedCategories}
        onCategoriesChange={setSelectedCategories}
        spicyLevel={spicyLevel}
        onSpicyLevelChange={setSpicyLevel}
        priceRange={priceRange}
        onPriceRangeChange={setPriceRange}
      />

      <div className="my-8 flex justify-center">
        <SpinWheel
          foods={getFilteredFoods().length > 0 ? getFilteredFoods() : foods}
          onSpin={handleSpin}
          onSpinEnd={handleSpinEnd}
          isSpinning={isSpinning}
          selectedFood={selectedFood}
        />
      </div>

      {selectedFood && !isSpinning && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <FoodCard food={selectedFood} onFeedback={handleFeedback} />
        </div>
      )}

      <div className="my-8" />

      <HistoryPanel
        history={history}
        onClear={handleClearHistory}
      />

      <div className="mt-8 text-center text-xs text-muted-foreground">
        <p>
          {useBackend ? "✨ 已连接 seekdb + PowerContext" : "📱 本地模式运行中"}
        </p>
        <p className="mt-1">
          数据存储：{useBackend ? "云端" : "本地浏览器"}
        </p>
      </div>
    </main>
  );
}
