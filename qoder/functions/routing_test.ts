import { isKnownRoute, normalizeApiPath } from "./routing.mjs";

function eq(actual: unknown, expected: unknown, label: string) {
  if (actual !== expected) {
    throw new Error(`${label}: ${JSON.stringify(actual)} !== ${JSON.stringify(expected)}`);
  }
}

const cases: Array<[string, string]> = [
  ["/functions/v1/app", "/"],
  ["/functions/v1/app/", "/"],
  ["/functions/v1/app/api/foods", "/api/foods"],
  ["/functions/v1/app/api/foods/", "/api/foods"],
  ["/functions/v1/app/api/services/status", "/api/services/status"],
  ["/app", "/"],
  ["/app/api/foods", "/api/foods"],
  ["/app/api/services/status/", "/api/services/status"],
  ["/api/foods/", "/api/foods"],
  ["/", "/"],
  ["/v1/app", "/"],
  ["/v1/app/api/user/history/clear", "/api/user/history/clear"],
  ["/functions/v1/app/functions/v1/app/api/feedback", "/api/feedback"],
  ["/apple", "/apple"],
];

Deno.test("normalizeApiPath strips gateway prefixes and trailing slashes", () => {
  for (const [input, expected] of cases) {
    eq(normalizeApiPath(input), expected, input);
  }
  eq(isKnownRoute("/apple"), false, "unknown");
  eq(isKnownRoute("/api/foods/search"), true, "search route");
  eq(isKnownRoute("/"), true, "health");
});
