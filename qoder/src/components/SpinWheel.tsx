import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import type { Food } from "../data/foods";

interface SpinWheelProps {
  foods: Food[];
  onSpin: () => void;
  onSpinEnd: () => void;
  isSpinning: boolean;
  selectedFood: Food | null;
}

export function SpinWheel({ foods, onSpin, onSpinEnd, isSpinning, selectedFood }: SpinWheelProps) {
  const [rotation, setRotation] = useState(0);
  const [displayFood, setDisplayFood] = useState<Food | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const colors = [
    "#f54900", "#009689", "#104e64", "#ffb900", "#fe9a00",
    "#8e51ff", "#00bc7d", "#ff2056", "#ad46ff", "#171717",
  ];

  const handleSpin = () => {
    if (isSpinning) return;
    onSpin();

    const spins = 5 + Math.random() * 5;
    const targetRotation = rotation + spins * 360;
    const duration = 3000;
    const startTime = Date.now();
    const startRotation = rotation;

    intervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentRotation = startRotation + (targetRotation - startRotation) * easeOut;
      setRotation(currentRotation);

      const idx = Math.floor((currentRotation / 30) % Math.min(foods.length, 10));
      setDisplayFood(foods[idx % foods.length]);

      if (progress >= 1) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setDisplayFood(selectedFood);
        onSpinEnd();
      }
    }, 16);
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const sliceCount = Math.min(foods.length, 10);
  const sliceAngle = 360 / sliceCount;

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative">
        <div
          className="absolute -top-4 left-1/2 z-10 -translate-x-1/2 text-4xl"
          style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.3))" }}
        >
          ▼
        </div>

        <div
          className="relative h-64 w-64 rounded-full border-4 border-primary shadow-xl transition-transform md:h-80 md:w-80"
          style={{
            transform: `rotate(${rotation}deg)`,
            background: `conic-gradient(${Array.from({ length: sliceCount }, (_, i) =>
              `${colors[i % colors.length]} ${i * sliceAngle}deg ${(i + 1) * sliceAngle}deg`
            ).join(", ")})`,
          }}
        >
          {foods.slice(0, sliceCount).map((food, i) => {
            const angle = i * sliceAngle + sliceAngle / 2;
            const rad = (angle - 90) * (Math.PI / 180);
            const radius = 38;
            const x = 50 + radius * Math.cos(rad);
            const y = 50 + radius * Math.sin(rad);
            return (
              <div
                key={food.id}
                className="absolute text-2xl md:text-3xl"
                style={{
                  left: `${x}%`,
                  top: `${y}%`,
                  transform: `translate(-50%, -50%) rotate(${-rotation}deg)`,
                }}
              >
                {food.emoji}
              </div>
            );
          })}
        </div>
      </div>

      <div className="h-16 text-center">
        {isSpinning && displayFood && (
          <div className="animate-pulse text-2xl font-bold">
            {displayFood.emoji} {displayFood.name}
          </div>
        )}
        {!isSpinning && selectedFood && (
          <div className="text-xl font-semibold text-primary">
            就决定是：{selectedFood.name}！
          </div>
        )}
      </div>

      <Button
        size="lg"
        onClick={handleSpin}
        disabled={isSpinning}
        className="h-14 px-8 text-lg font-semibold"
      >
        {isSpinning ? "转动中..." : "🎰 转一转"}
      </Button>
    </div>
  );
}
