/**
 * Connectivity check for embedded seekdb hybrid search.
 * Vectors here are synthetic and supplied by the caller. The web app does not use this path.
 */
import { closeSeekdb, hybridSearch, openSeekdb, resetCollection, upsertChunks } from "../server/seekdb.js";

function axis(index: number): number[] {
  const vector = new Array<number>(384).fill(0);
  vector[index] = 1;
  return vector;
}

async function main(): Promise<void> {
  await openSeekdb();
  await resetCollection();
  const importedAt = new Date().toISOString();
  await upsertChunks([
    {
      id: "smoke-fulltext",
      document: "星澜混合检索暗号 DBMS_HYBRID_SEARCH 只出现在全文这一篇。",
      embedding: axis(0),
      metadata: {
        source: "smoke-fulltext.txt",
        title: "fulltext",
        chunkIndex: 0,
        importedAt,
        model: "synthetic",
        dtype: "none",
        device: "smoke",
      },
    },
    {
      id: "smoke-vector",
      document: "这篇只有向量靠近查询，正文是西湖龙井与茶园。",
      embedding: axis(1),
      metadata: {
        source: "smoke-vector.txt",
        title: "vector",
        chunkIndex: 0,
        importedAt,
        model: "synthetic",
        dtype: "none",
        device: "smoke",
      },
    },
  ]);

  const fused = await hybridSearch({
    query: "DBMS_HYBRID_SEARCH",
    embedding: axis(1),
    nResults: 5,
  });
  const ids = fused.hits.map((hit) => hit.id);
  if (!ids.includes("smoke-fulltext") || !ids.includes("smoke-vector")) {
    throw new Error(`hybrid search did not return both channels: ${ids.join(",")}`);
  }
  if (fused.fusedIn !== "seekdb") throw new Error("fusion flag missing");

  await upsertChunks([
    {
      id: "smoke-incremental",
      document: "稍后写入的星澜增量文档，用来检查刷新后的可见性。",
      embedding: axis(2),
      metadata: {
        source: "smoke-incremental.txt",
        title: "incremental",
        chunkIndex: 0,
        importedAt: new Date().toISOString(),
        model: "synthetic",
        dtype: "none",
        device: "smoke",
      },
    },
  ]);
  const incremental = await hybridSearch({
    query: "星澜增量文档",
    embedding: axis(2),
    nResults: 5,
  });
  if (!incremental.hits.some((hit) => hit.id === "smoke-incremental")) {
    throw new Error(`incremental doc missing after refresh: ${incremental.hits.map((hit) => hit.id).join(",")}`);
  }

  await resetCollection();
  console.log("smoke ok", { hybridIds: ids, incremental: incremental.hits.map((hit) => hit.id) });
  await closeSeekdb();
}

main().catch(async (error) => {
  console.error(error);
  try {
    await closeSeekdb();
  } catch {
    // already closed or never opened
  }
  process.exit(1);
});
