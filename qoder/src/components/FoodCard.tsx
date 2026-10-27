import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Food } from "../data/foods";

interface FoodCardProps {
  food: Food;
  onFeedback: (liked: boolean) => void;
}

const priceLabels = { low: "💰 实惠", medium: "💰💰 适中", high: "💰💰💰 小贵" };
const spicyLabels = ["不辣", "微辣", "中辣", "爆辣"];

export function FoodCard({ food, onFeedback }: FoodCardProps) {
  return (
    <Card className="mx-auto max-w-md border-2 border-primary/20 shadow-lg">
      <CardHeader className="text-center">
        <div className="mb-2 text-6xl">{food.emoji}</div>
        <CardTitle className="text-2xl">{food.name}</CardTitle>
        <p className="text-sm text-muted-foreground">{food.description}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap justify-center gap-2">
          {food.tags.map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
            </Badge>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-sm">
          <div className="rounded-lg bg-muted p-2">
            <div className="text-lg">{priceLabels[food.priceRange].split(" ")[0]}</div>
            <div className="text-xs text-muted-foreground">{priceLabels[food.priceRange].split(" ")[1]}</div>
          </div>
          <div className="rounded-lg bg-muted p-2">
            <div className="text-lg">{"🌶️".repeat(food.spicy) || "✓"}</div>
            <div className="text-xs text-muted-foreground">{spicyLabels[food.spicy]}</div>
          </div>
          <div className="rounded-lg bg-muted p-2">
            <div className="text-lg">{"⭐".repeat(Math.ceil(food.healthScore / 2))}</div>
            <div className="text-xs text-muted-foreground">健康指数</div>
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => onFeedback(false)}
          >
            😕 不想吃
          </Button>
          <Button
            className="flex-1"
            onClick={() => onFeedback(true)}
          >
            😋 就这个！
          </Button>
        </div>

        <div className="text-center text-xs text-muted-foreground">
          反馈会帮助系统更懂你的口味
        </div>
      </CardContent>
    </Card>
  );
}
