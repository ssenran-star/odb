import type { ChunkMetadata } from "./types";

export type SeekdbState = {
  ok: boolean;
  mode: string;
  database: string;
  collection: string;
  dimension: number;
  distance: string;
  analyzer: string;
  ngramTokenSize: number;
  embeddingFunction: null;
  count: number;
  lastImportAt: string | null;
  lastRefreshAt: string | null;
  lastRefreshNote: string | null;
  version: string;
};

export type SampleFile = {
  name: string;
  bytes: number;
  incremental: boolean;
};

export type SearchHit = {
  rank: number;
  id: string;
  document: string;
  score: number;
  metadata: ChunkMetadata | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  const text = await response.text();
  const body = text ? (JSON.parse(text) as T & { error?: string }) : ({} as T);
  if (!response.ok) {
    throw new Error((body as { error?: string }).error || response.statusText);
  }
  return body;
}

export function fetchState(): Promise<SeekdbState> {
  return request<SeekdbState>("/api/state");
}

export function fetchSamples(): Promise<{ files: SampleFile[] }> {
  return request("/api/samples");
}

export function fetchSampleText(name: string): Promise<string> {
  return fetch(`/api/samples/${encodeURIComponent(name)}`).then(async (response) => {
    if (!response.ok) throw new Error(await response.text());
    return response.text();
  });
}

export function postDocuments(chunks: Array<{
  id: string;
  document: string;
  embedding: number[];
  metadata: ChunkMetadata;
}>): Promise<{ upserted: number; count: number; refreshedAt: string; refreshNote: string }> {
  return request("/api/documents", {
    method: "POST",
    body: JSON.stringify({ chunks }),
  });
}

export function postSearch(input: {
  query: string;
  embedding: number[];
  nResults: number;
}): Promise<{ query: string; hits: SearchHit[]; fusedIn: "seekdb" }> {
  return request("/api/search", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function postRefresh(): Promise<{ refreshedAt: string; note: string }> {
  return request("/api/refresh", { method: "POST" });
}

export function postReset(): Promise<{ count: number }> {
  return request("/api/reset", { method: "POST" });
}
