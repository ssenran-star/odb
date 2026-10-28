import { handler } from "../functions/handler.ts";

const port = Number(Deno.env.get("PORT") || "8000");
const hostname = Deno.env.get("HOST") || "127.0.0.1";

console.log(`今天吃什么 function listening on http://${hostname}:${port}`);
Deno.serve({ hostname, port }, (request) => handler(request));
