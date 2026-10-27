import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Food } from "../data/foods";
import type { HistoryItem } from "../lib/api";

interface HistoryPanelProps {
  history: HistoryItem[];
  onClear: () => void;
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "刚刚";
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;
  return date.toLocaleDateString("zh-CN");
}

export function HistoryPanel({ history, onClear }: HistoryPanelProps) {
  if (history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">📋 历史记录</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground">
            还没有记录，转一转开始你的美食之旅吧！
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">📋 历史记录</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClear}>
          清空
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {history.slice(0, 10).map((item, idx) => {
            const food = item.food;
            const key = `${item.foodId || food?.id || idx}-${item.timestamp}`;
            return (
              <div
                key={key}
                className="flex items-center justify-between rounded-lg bg-muted/50 p-3"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{food?.emoji || "🍽️"}</span>
                  <div>
                    <div className="font-medium">{food?.name || "未知菜品"}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatTime(item.timestamp)}
                    </div>
                  </div>
                </div>
                <div className="text-xl">
                  {item.liked === true && "😋"}
                  {item.liked === false && "😕"}
                  {item.liked === null && "🤔"}
                </div>
              </div>
            );
          })}
        </div>
        {history.length > 10 && (
          <p className="mt-3 text-center text-sm text-muted-foreground">
            还有 {history.length - 10} 条记录...
          </p>
        )}
      </CardContent>
    </Card>
  );
}
