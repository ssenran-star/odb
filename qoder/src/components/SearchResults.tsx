import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Food } from "../data/foods";

interface SearchResultsProps {
  results: Food[];
  onSelect: (food: Food) => void;
  onClose: () => void;
}

export function SearchResults({ results, onSelect, onClose }: SearchResultsProps) {
  return (
    <Card className="mb-6 border-primary/30">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">🔍 搜索结果</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ✕
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {results.map((food) => (
            <div
              key={food.id}
              className="flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors hover:border-primary hover:bg-primary/5"
              onClick={() => onSelect(food)}
            >
              <span className="text-3xl">{food.emoji}</span>
              <div className="flex-1">
                <div className="font-medium">{food.name}</div>
                <div className="text-xs text-muted-foreground">{food.description}</div>
                <div className="mt-1 flex gap-1">
                  {food.tags.slice(0, 2).map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        {results.length === 0 && (
          <p className="text-center text-muted-foreground">没有找到匹配的菜品</p>
        )}
      </CardContent>
    </Card>
  );
}
