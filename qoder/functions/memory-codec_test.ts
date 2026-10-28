import { decodeHistory, decodePreferences, encodeHistory, encodePreferences } from "./memory-codec.ts";

Deno.test("preferences round-trip keeps structured fields and spicy zero", () => {
  const text = encodePreferences("user_a", {
    favoriteCategories: ["noodle"],
    spicyLevel: 0,
    priceRange: "low",
    dislikedFoods: ["3"],
    favoriteFoods: ["1"],
  }, (id) => (id === "1" ? "红烧牛肉面" : id), 100);
  if (!text.includes("用户 user_a 偏好")) throw new Error("summary missing");
  if (!text.includes("红烧牛肉面")) throw new Error("food name missing");
  const decoded = decodePreferences(text);
  if (!decoded) throw new Error("decode failed");
  if (decoded.userId !== "user_a" || decoded.updatedAt !== 100) throw new Error("identity");
  if (decoded.prefs.spicyLevel !== 0) throw new Error("spicy");
  if (decoded.prefs.favoriteFoods[0] !== "1") throw new Error("favorite");
  if (decodePreferences("no marker") !== null) throw new Error("plain text should not decode");
});

Deno.test("history round-trip keeps liked null", () => {
  const text = encodeHistory("user_b", [
    { foodId: "2", timestamp: 50, liked: true },
    { foodId: "5", timestamp: 40, liked: null },
  ], (id) => id, 60);
  const decoded = decodeHistory(text);
  if (!decoded || decoded.items.length !== 2) throw new Error("items");
  if (decoded.items[1].liked !== null) throw new Error("null liked");
  if (!text.includes("最近吃过")) throw new Error("summary");
});
