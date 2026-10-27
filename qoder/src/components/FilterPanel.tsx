import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface Category {
  id: string;
  name: string;
  emoji: string;
}

interface FilterPanelProps {
  categories: Category[];
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  spicyLevel: number | null;
  onSpicyLevelChange: (level: number | null) => void;
  priceRange: string | null;
  onPriceRangeChange: (range: string | null) => void;
}

export function FilterPanel({
  categories,
  selectedCategories,
  onCategoriesChange,
  spicyLevel,
  onSpicyLevelChange,
  priceRange,
  onPriceRangeChange,
}: FilterPanelProps) {
  const toggleCategory = (id: string) => {
    if (selectedCategories.includes(id)) {
      onCategoriesChange(selectedCategories.filter((c) => c !== id));
    } else {
      onCategoriesChange([...selectedCategories, id]);
    }
  };

  const toggleSpicy = (level: number) => {
    onSpicyLevelChange(spicyLevel === level ? null : level);
  };

  const togglePrice = (range: string) => {
    onPriceRangeChange(priceRange === range ? null : range);
  };

  const hasFilters = selectedCategories.length > 0 || spicyLevel !== null || priceRange !== null;

  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <div>
          <div className="mb-2 text-sm font-medium">🍱 菜系</div>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <Badge
                key={cat.id}
                variant={selectedCategories.includes(cat.id) ? "default" : "outline"}
                className="cursor-pointer px-3 py-1 text-sm transition-colors hover:bg-primary/10"
                onClick={() => toggleCategory(cat.id)}
              >
                {cat.emoji} {cat.name}
              </Badge>
            ))}
          </div>
        </div>

        <Separator />

        <div>
          <div className="mb-2 text-sm font-medium">🌶️ 辣度</div>
          <div className="flex flex-wrap gap-2">
            {[
              { level: 0, label: "不辣" },
              { level: 1, label: "微辣" },
              { level: 2, label: "中辣" },
              { level: 3, label: "爆辣" },
            ].map(({ level, label }) => (
              <Badge
                key={level}
                variant={spicyLevel === level ? "default" : "outline"}
                className="cursor-pointer px-3 py-1 transition-colors hover:bg-primary/10"
                onClick={() => toggleSpicy(level)}
              >
                {"🌶️".repeat(level) || "✓"} {label}
              </Badge>
            ))}
          </div>
        </div>

        <Separator />

        <div>
          <div className="mb-2 text-sm font-medium">💰 价位</div>
          <div className="flex flex-wrap gap-2">
            {[
              { range: "low", label: "实惠" },
              { range: "medium", label: "适中" },
              { range: "high", label: "小贵" },
            ].map(({ range, label }) => (
              <Badge
                key={range}
                variant={priceRange === range ? "default" : "outline"}
                className="cursor-pointer px-3 py-1 transition-colors hover:bg-primary/10"
                onClick={() => togglePrice(range)}
              >
                {label}
              </Badge>
            ))}
          </div>
        </div>

        {hasFilters && (
          <>
            <Separator />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onCategoriesChange([]);
                onSpicyLevelChange(null);
                onPriceRangeChange(null);
              }}
            >
              清除筛选
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
