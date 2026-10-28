import fs from "node:fs/promises";
import path from "node:path";
import {
  FulltextIndexConfig,
  Schema,
  SeekdbAdminClient,
  SeekdbClient,
  VectorIndexConfig,
} from "seekdb";
import {
  INCREMENTAL_SAMPLES,
  SAMPLES_DIR,
  loadConfig,
  type AppConfig,
} from "./config.js";

export const EMBED_DIM = 384;

export type ChunkMetadata = {
  source: string;
  title: string;
  chunkIndex: number;
  importedAt: string;
  model: string;
  dtype: string;
  device: string;
};

export type ChunkInput = {
  id: string;
  document: string;
  embedding: number[];
  metadata: ChunkMetadata;
};

export type SearchHit = {
  rank: number;
  id: string;
  document: string;
  score: number;
  metadata: ChunkMetadata | null;
};

type SessionRow = {
  docCount: number;
  lastImportAt: string | null;
  lastRefreshAt: string | null;
  lastRefreshNote: string | null;
};

let client: SeekdbClient | null = null;
let collection: Awaited<ReturnType<SeekdbClient["getOrCreateCollection"]>> | null =
  null;
let config: AppConfig | null = null;
let versionText = "";
let session: SessionRow = {
  docCount: 0,
  lastImportAt: null,
  lastRefreshAt: null,
  lastRefreshNote: null,
};

function requireOpen(): {
  client: SeekdbClient;
  collection: NonNullable<typeof collection>;
  config: AppConfig;
} {
  if (!client || !collection || !config) {
    throw new Error("seekdb is not open");
  }
  return { client, collection, config };
}

function databaseName(entry: unknown): string {
  if (typeof entry === "string") return entry;
  if (entry && typeof entry === "object" && "name" in entry) {
    return String((entry as { name: unknown }).name);
  }
  return "";
}

function assertEmbedding(vector: number[], id: string): void {
  if (!Array.isArray(vector) || vector.length !== EMBED_DIM) {
    throw new Error(`chunk ${id} embedding must be length ${EMBED_DIM}`);
  }
  for (let i = 0; i < vector.length; i += 1) {
    const value = vector[i];
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new Error(`chunk ${id} embedding contains a non-finite value`);
    }
  }
}

function assertChunk(chunk: ChunkInput): void {
  if (!chunk.id || chunk.id.length > 240) throw new Error("invalid chunk id");
  if (!chunk.document || chunk.document.length > 8000) {
    throw new Error(`chunk ${chunk.id} document is empty or too long`);
  }
  assertEmbedding(chunk.embedding, chunk.id);
  const meta = chunk.metadata;
  if (!meta?.source || !meta.title || !meta.model || !meta.dtype || !meta.device) {
    throw new Error(`chunk ${chunk.id} is missing metadata`);
  }
  if (!Number.isInteger(meta.chunkIndex) || meta.chunkIndex < 0) {
    throw new Error(`chunk ${chunk.id} has a bad chunkIndex`);
  }
}

export async function openSeekdb(): Promise<void> {
  config = loadConfig();
  await fs.mkdir(config.path, { recursive: true });

  const admin = new SeekdbAdminClient({ path: config.path });
  const databases = await admin.listDatabases();
  const names = databases.map(databaseName);
  if (!names.includes(config.database)) {
    await admin.createDatabase(config.database);
  }
  await admin.close();

  client = new SeekdbClient({
    path: config.path,
    database: config.database,
  });

  const schema = new Schema()
    .createIndex(
      new VectorIndexConfig({
        hnsw: { dimension: config.dimension, distance: config.distance },
        embeddingFunction: null,
      })
    )
    .createIndex(
      new FulltextIndexConfig(config.fulltext.analyzer, {
        ngram_token_size: config.fulltext.ngram_token_size,
      })
    );

  collection = await client.getOrCreateCollection({
    name: config.collection,
    schema,
    embeddingFunction: null,
  });

  const described = await collection.describe();
  if (described.dimension !== config.dimension) {
    throw new Error(
      `collection ${config.collection} dimension is ${described.dimension}, expected ${config.dimension}`
    );
  }

  const versionRows = await client.execute("SELECT VERSION() AS version");
  versionText = readVersion(versionRows);
  await ensureSessionTable();
  session = await readSession();
  session.docCount = await collection.count();
  await writeSession();
}

function readVersion(rows: unknown): string {
  if (!Array.isArray(rows) || rows.length === 0) return "";
  const row = rows[0] as Record<string, unknown>;
  const value = row.version ?? row.VERSION ?? Object.values(row)[0];
  return value == null ? "" : String(value);
}

async function ensureSessionTable(): Promise<void> {
  const { client: db } = requireOpen();
  await db.execute(`
    CREATE TABLE IF NOT EXISTS kb_session (
      id VARCHAR(64) PRIMARY KEY,
      collection_name VARCHAR(128) NOT NULL,
      dimension INT NOT NULL,
      distance_metric VARCHAR(32) NOT NULL,
      analyzer VARCHAR(32) NOT NULL,
      doc_count INT NOT NULL,
      last_import_at VARCHAR(40) NULL,
      last_refresh_at VARCHAR(40) NULL,
      last_refresh_note VARCHAR(255) NULL
    )
  `);
}

async function readSession(): Promise<SessionRow> {
  const { client: db } = requireOpen();
  const rows = await db.execute(
    "SELECT doc_count, last_import_at, last_refresh_at, last_refresh_note FROM kb_session WHERE id = ?",
    ["main"]
  );
  if (!rows || rows.length === 0) {
    return {
      docCount: 0,
      lastImportAt: null,
      lastRefreshAt: null,
      lastRefreshNote: null,
    };
  }
  const row = rows[0] as Record<string, unknown>;
  return {
    docCount: Number(row.doc_count ?? 0),
    lastImportAt: nullableString(row.last_import_at),
    lastRefreshAt: nullableString(row.last_refresh_at),
    lastRefreshNote: nullableString(row.last_refresh_note),
  };
}

function nullableString(value: unknown): string | null {
  if (value == null) return null;
  const text = String(value);
  return text.length === 0 ? null : text;
}

async function writeSession(): Promise<void> {
  const { client: db, config: cfg } = requireOpen();
  await db.execute("DELETE FROM kb_session WHERE id = ?", ["main"]);
  await db.execute(
    `INSERT INTO kb_session
      (id, collection_name, dimension, distance_metric, analyzer, doc_count, last_import_at, last_refresh_at, last_refresh_note)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      "main",
      cfg.collection,
      cfg.dimension,
      cfg.distance,
      cfg.fulltext.analyzer,
      session.docCount,
      session.lastImportAt,
      session.lastRefreshAt,
      session.lastRefreshNote,
    ]
  );
}

export async function getState(): Promise<Record<string, unknown>> {
  const { collection: col, config: cfg } = requireOpen();
  const described = await col.describe();
  const count = await col.count();
  session.docCount = count;
  return {
    ok: true,
    mode: "embedded",
    path: cfg.path,
    database: cfg.database,
    collection: col.name,
    dimension: described.dimension,
    distance: described.distance,
    analyzer: cfg.fulltext.analyzer,
    ngramTokenSize: cfg.fulltext.ngram_token_size,
    embeddingFunction: null,
    count,
    lastImportAt: session.lastImportAt,
    lastRefreshAt: session.lastRefreshAt,
    lastRefreshNote: session.lastRefreshNote,
    version: versionText,
  };
}

export async function listSamples(): Promise<
  Array<{ name: string; bytes: number; incremental: boolean }>
> {
  const entries = await fs.readdir(SAMPLES_DIR);
  const files = entries.filter((name) => name.endsWith(".txt")).sort();
  const listed = [];
  for (const name of files) {
    const stat = await fs.stat(path.join(SAMPLES_DIR, name));
    listed.push({
      name,
      bytes: stat.size,
      incremental: INCREMENTAL_SAMPLES.has(name),
    });
  }
  return listed;
}

export async function readSample(name: string): Promise<string> {
  if (!/^[\w.-]+$/.test(name) || !name.endsWith(".txt")) {
    throw new Error("unknown sample");
  }
  const full = path.join(SAMPLES_DIR, name);
  if (path.dirname(full) !== SAMPLES_DIR) throw new Error("unknown sample");
  return fs.readFile(full, "utf8");
}

export async function upsertChunks(chunks: ChunkInput[]): Promise<{
  upserted: number;
  count: number;
  refreshedAt: string;
  refreshNote: string;
}> {
  if (chunks.length === 0) throw new Error("no chunks");
  if (chunks.length > 200) throw new Error("too many chunks in one request");
  const seen = new Set<string>();
  for (const chunk of chunks) {
    assertChunk(chunk);
    if (seen.has(chunk.id)) throw new Error(`duplicate id ${chunk.id}`);
    seen.add(chunk.id);
  }

  const { collection: col } = requireOpen();
  await col.upsert({
    ids: chunks.map((chunk) => chunk.id),
    documents: chunks.map((chunk) => chunk.document),
    embeddings: chunks.map((chunk) => chunk.embedding),
    metadatas: chunks.map((chunk) => chunk.metadata),
  });

  const refresh = await refreshIndex();
  session.docCount = await col.count();
  session.lastImportAt = new Date().toISOString();
  await writeSession();
  return {
    upserted: chunks.length,
    count: session.docCount,
    refreshedAt: refresh.refreshedAt,
    refreshNote: refresh.note,
  };
}

export async function refreshIndex(): Promise<{
  refreshedAt: string;
  note: string;
}> {
  const { client: db, collection: col } = requireOpen();
  const notes: string[] = [];
  const refresher = col as { refresh_index?: () => Promise<void> };
  try {
    if (refresher.refresh_index) {
      await refresher.refresh_index();
      notes.push("collection.refresh_index()");
    }
  } catch (error) {
    notes.push(`refresh_index skipped: ${(error as Error).message}`);
  }
  try {
    await db.execute("CALL dbms_index_manager.refresh();");
    if (!notes.includes("collection.refresh_index()")) {
      notes.push("CALL dbms_index_manager.refresh()");
    }
  } catch (error) {
    notes.push(`dbms_index_manager.refresh skipped: ${(error as Error).message}`);
  }
  const refreshedAt = new Date().toISOString();
  session.lastRefreshAt = refreshedAt;
  session.lastRefreshNote = notes.join(" | ").slice(0, 255);
  session.docCount = await col.count();
  await writeSession();
  return { refreshedAt, note: session.lastRefreshNote };
}

export async function hybridSearch(input: {
  query: string;
  embedding: number[];
  nResults?: number;
}): Promise<{ query: string; hits: SearchHit[]; fusedIn: "seekdb" }> {
  const query = input.query.replace(/\s+/g, " ").trim();
  if (!query || query.length > 300) throw new Error("query is empty or too long");
  assertEmbedding(input.embedding, "query");
  const nResults = Math.min(Math.max(input.nResults ?? 5, 1), 20);
  const { collection: col } = requireOpen();

  // One seekdb call. DBMS_HYBRID_SEARCH fuses full-text and KNN inside the engine.
  const result = await col.hybridSearch({
    query: {
      whereDocument: { $contains: query },
      nResults: Math.max(nResults, 10),
    },
    knn: {
      queryEmbeddings: [input.embedding],
      nResults: Math.max(nResults, 10),
    },
    rank: { rrf: {} },
    nResults,
    include: ["documents", "metadatas", "distances"],
  });

  const ids = result.ids?.[0] ?? [];
  const documents = result.documents?.[0] ?? [];
  const metadatas = result.metadatas?.[0] ?? [];
  const distances = result.distances?.[0] ?? [];
  const hits: SearchHit[] = ids.map((id, index) => ({
    rank: index + 1,
    id: String(id),
    document: documents[index] == null ? "" : String(documents[index]),
    score: Number(distances[index] ?? 0),
    metadata: (metadatas[index] as ChunkMetadata | null) ?? null,
  }));
  return { query, hits, fusedIn: "seekdb" };
}

export async function resetCollection(): Promise<{ count: number }> {
  const { collection: col } = requireOpen();
  const existing = await col.get({ include: [] });
  const ids = [...(existing.ids ?? [])];
  if (ids.length > 0) {
    await col.delete({ ids });
  }
  session.docCount = await col.count();
  session.lastImportAt = null;
  await refreshIndex();
  return { count: session.docCount };
}

export async function closeSeekdb(): Promise<void> {
  if (client) await client.close();
  client = null;
  collection = null;
}
