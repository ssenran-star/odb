import http from "node:http";
import {
  closeSeekdb,
  getState,
  hybridSearch,
  listSamples,
  openSeekdb,
  readSample,
  refreshIndex,
  resetCollection,
  upsertChunks,
  type ChunkInput,
} from "./seekdb.js";
import { loadConfig } from "./config.js";
import { enqueue } from "./queue.js";

const config = loadConfig();

function sendJson(res: http.ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "content-type",
    "cache-control": "no-store",
  });
  res.end(payload);
}

async function readJson(req: http.IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req) {
    const buf = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    size += buf.length;
    if (size > 32 * 1024 * 1024) throw new Error("body too large");
    chunks.push(buf);
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

const server = http.createServer(async (req, res) => {
  try {
    if (!req.url || !req.method) {
      sendJson(res, 400, { error: "bad request" });
      return;
    }
    if (req.method === "OPTIONS") {
      sendJson(res, 204, {});
      return;
    }
    const url = new URL(req.url, `http://${config.host}:${config.port}`);

    if (req.method === "GET" && url.pathname === "/api/state") {
      sendJson(res, 200, await enqueue(() => getState()));
      return;
    }
    if (req.method === "GET" && url.pathname === "/api/samples") {
      sendJson(res, 200, { files: await listSamples() });
      return;
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/samples/")) {
      const name = decodeURIComponent(url.pathname.slice("/api/samples/".length));
      const text = await readSample(name);
      res.writeHead(200, {
        "content-type": "text/plain; charset=utf-8",
        "access-control-allow-origin": "*",
        "cache-control": "no-store",
      });
      res.end(text);
      return;
    }
    if (req.method === "POST" && url.pathname === "/api/documents") {
      const body = (await readJson(req)) as { chunks?: ChunkInput[] };
      const result = await enqueue(() => upsertChunks(body.chunks ?? []));
      sendJson(res, 200, result);
      return;
    }
    if (req.method === "POST" && url.pathname === "/api/search") {
      const body = (await readJson(req)) as {
        query?: string;
        embedding?: number[];
        nResults?: number;
      };
      if (!body.query || !body.embedding) {
        sendJson(res, 400, { error: "query and browser embedding are required" });
        return;
      }
      const query = body.query;
      const embedding = body.embedding;
      const nResults = body.nResults;
      const result = await enqueue(() =>
        hybridSearch({
          query,
          embedding,
          nResults,
        })
      );
      sendJson(res, 200, result);
      return;
    }
    if (req.method === "POST" && url.pathname === "/api/refresh") {
      sendJson(res, 200, await enqueue(() => refreshIndex()));
      return;
    }
    if (req.method === "POST" && url.pathname === "/api/reset") {
      sendJson(res, 200, await enqueue(() => resetCollection()));
      return;
    }
    sendJson(res, 404, { error: "not found" });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(req.method, req.url, message);
    sendJson(res, 500, { error: message });
  }
});

await openSeekdb();
server.listen(config.port, config.host, () => {
  console.log(
    `seekdb embedded api http://${config.host}:${config.port} db=${config.database} collection=${config.collection}`
  );
  console.log("embeddings are not computed in this process");
});

async function shutdown(): Promise<void> {
  server.close();
  await closeSeekdb();
  process.exit(0);
}

process.on("SIGINT", () => {
  void shutdown();
});
process.on("SIGTERM", () => {
  void shutdown();
});
