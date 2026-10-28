import { handler } from "./handler.ts";

function assert(condition: unknown, message: string) {
  if (!condition) throw new Error(message);
}

async function json(pathname: string, init?: RequestInit) {
  const response = await handler(new Request(`http://function.local${pathname}`, init));
  const body = await response.json();
  return { status: response.status, body };
}

Deno.test("health and food routes accept prefixed, stripped, and slashed paths", async () => {
  for (const pathname of ["/functions/v1/app", "/functions/v1/app/", "/app", "/"]) {
    const { status, body } = await json(pathname);
    assert(status === 200 && body.ok === true, `${pathname} ${status} ${JSON.stringify(body)}`);
    assert(body.services.powerContext === "unconfigured", "health must not claim PowerContext");
    assert(body.services.seekdb === "unconfigured", "health must not claim seekdb");
  }

  for (const pathname of [
    "/functions/v1/app/api/foods",
    "/functions/v1/app/api/foods/",
    "/app/api/foods",
    "/api/foods",
  ]) {
    const { status, body } = await json(pathname);
    assert(status === 200 && Array.isArray(body.data) && body.data.length >= 20, pathname);
    assert(body.source === "catalog", "catalog listing is not seekdb");
  }

  const missing = await json("/functions/v1/app/missing");
  assert(missing.status === 404, "unknown");
  assert(missing.body.receivedPath === "/functions/v1/app/missing", "received path");
  assert(missing.body.path === "/missing", "normalized path");
});

Deno.test("keyword search and preference memory work in demo mode", async () => {
  const search = await json(`/api/foods/search?q=${encodeURIComponent("辣")}`);
  assert(search.status === 200 && search.body.searchMethod === "keyword", JSON.stringify(search.body.searchMethod));
  assert(search.body.source === "local", "demo search source");
  const names = search.body.data.map((food: { name: string }) => food.name);
  for (const name of ["麻辣火锅", "麻辣烫", "酸菜鱼"]) {
    assert(names.includes(name), `missing ${name}`);
  }

  const userId = "verify-demo";
  const saved = await json(`/api/user/preferences?userId=${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ favoriteCategories: ["noodle"], favoriteFoods: ["1"], dislikedFoods: ["2"] }),
  });
  assert(saved.status === 200 && saved.body.memorySource === "local", "demo write");

  const loaded = await json(`/api/user/preferences?userId=${userId}`);
  assert(loaded.body.data.favoriteCategories[0] === "noodle", "prefs persisted in process");

  const random = await json(`/api/foods/random?userId=${userId}`);
  assert(random.body.data.category === "noodle", `expected noodle, got ${random.body.data?.category}`);
  assert(random.body.memorySource === "local", "demo random");

  const status = await json("/app/api/services/status");
  assert(status.status === 200, "status");
  assert(status.body.mode === "demo", "demo mode");
  assert(status.body.services.powerContext.status === "unconfigured", "pc status");
  assert(status.body.services.seekdb.status === "unconfigured", "seek status");
  assert(status.body.services.powerContext.status !== "connected", "not connected");
});

Deno.test("forwarded URI is used only when the request path is not already a route", async () => {
  const response = await handler(new Request("http://function.local/ignored/extra", {
    headers: { "x-forwarded-uri": "/functions/v1/app/api/categories" },
  }));
  const body = await response.json();
  assert(response.status === 200 && Array.isArray(body.data), JSON.stringify(body));
});
