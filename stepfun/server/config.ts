import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export type AppConfig = {
  mode: "embedded";
  path: string;
  database: string;
  collection: string;
  host: string;
  port: number;
  dimension: number;
  distance: "cosine" | "l2" | "inner_product";
  fulltext: {
    analyzer: "ngram";
    ngram_token_size: number;
  };
};

export function loadConfig(): AppConfig {
  const file = path.join(root, "seekdb.config.json");
  const parsed = JSON.parse(readFileSync(file, "utf8")) as AppConfig;
  const port = Number(process.env.SEEKDB_PORT ?? parsed.port);
  return {
    ...parsed,
    path: path.resolve(root, process.env.SEEKDB_PATH ?? parsed.path),
    database: process.env.SEEKDB_DATABASE ?? parsed.database,
    host: process.env.SEEKDB_HOST ?? parsed.host,
    port,
  };
}

export const ROOT = root;
export const SAMPLES_DIR = path.join(root, "data", "samples");
export const INCREMENTAL_SAMPLES = new Set(["05-incremental-starlan.txt"]);
