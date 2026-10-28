import { env, pipeline } from "@huggingface/transformers";

type EmbeddingTensor = {
  data: ArrayLike<number>;
  dispose: () => void;
};

type Extractor = {
  (texts: string | string[], options?: { pooling?: "mean"; normalize?: boolean }): Promise<EmbeddingTensor>;
  dispose: () => Promise<void>;
};

const loadFeatureExtractor = pipeline as (
  task: "feature-extraction",
  model: string,
  options?: Record<string, unknown>
) => Promise<Extractor>;

export const MODEL_ID = "Xenova/all-MiniLM-L6-v2";
export const MODEL_REVISION = "751bff37182d3f1213fa05d7196b954e230abad9";
export const EMBED_DIM = 384;

export type RuntimeKind = {
  device: "webgpu" | "wasm";
  dtype: "fp16" | "q8";
  label: string;
};

env.allowLocalModels = false;
env.useBrowserCache = true;

let extractor: Extractor | null = null;
let active: RuntimeKind | null = null;
let pending: Promise<RuntimeKind> | null = null;
let forceWasm = false;

function configureWasm(): void {
  const wasm = env.backends.onnx.wasm;
  if (!wasm) return;
  wasm.numThreads = 1;
  wasm.proxy = false;
}

async function webgpuAvailable(): Promise<boolean> {
  if (forceWasm || !navigator.gpu) return false;
  try {
    const adapter = await navigator.gpu.requestAdapter();
    return adapter != null;
  } catch {
    return false;
  }
}

async function loadAttempt(
  attempt: { device: "webgpu" | "wasm"; dtype: "fp16" | "q8" },
  onProgress?: (message: string) => void
): Promise<Extractor> {
  onProgress?.(`加载 ${attempt.device} / ${attempt.dtype}`);
  return loadFeatureExtractor("feature-extraction", MODEL_ID, {
    device: attempt.device,
    dtype: attempt.dtype,
    revision: MODEL_REVISION,
    progress_callback: (progress: { status?: string; file?: string; progress?: number }) => {
      const info = progress as { status?: string; file?: string; progress?: number };
      if (info.status === "progress" && info.file) {
        onProgress?.(`${info.file} ${Math.round(info.progress ?? 0)}%`);
      } else if (info.status) {
        onProgress?.(`${info.status} ${info.file ?? ""}`.trim());
      }
    },
  });
}

export function getRuntime(): RuntimeKind | null {
  return active;
}

export async function initEmbedder(
  onProgress?: (message: string) => void
): Promise<RuntimeKind> {
  if (active) return active;
  if (pending) return pending;
  pending = (async () => {
    configureWasm();
    const gpu = await webgpuAvailable();
    const attempts: Array<{ device: "webgpu" | "wasm"; dtype: "fp16" | "q8" }> = gpu
      ? [
          { device: "webgpu", dtype: "fp16" },
          { device: "wasm", dtype: "q8" },
        ]
      : [{ device: "wasm", dtype: "q8" }];
    let lastError: unknown;
    for (const attempt of attempts) {
      try {
        extractor = await loadAttempt(attempt, onProgress);
        active = {
          ...attempt,
          label: attempt.device === "webgpu" ? "WebGPU · FP16" : "WASM · INT8",
        };
        return active;
      } catch (error) {
        lastError = error;
        extractor = null;
        console.warn("embedding backend failed", attempt, error);
      }
    }
    pending = null;
    throw lastError instanceof Error ? lastError : new Error(String(lastError));
  })();
  return pending;
}

function vectorsFromTensor(tensor: EmbeddingTensor, count: number): number[][] {
  const data = tensor.data as ArrayLike<number>;
  if (data.length !== count * EMBED_DIM) {
    throw new Error(`embedding rank mismatch: got ${data.length} values for ${count} texts`);
  }
  const rows: number[][] = [];
  for (let i = 0; i < count; i += 1) {
    const row = new Array<number>(EMBED_DIM);
    for (let j = 0; j < EMBED_DIM; j += 1) row[j] = Number(data[i * EMBED_DIM + j]);
    rows.push(row);
  }
  tensor.dispose();
  return rows;
}

async function runBatch(texts: string[]): Promise<number[][]> {
  if (!extractor) throw new Error("embedder is not ready");
  const tensor = await extractor(texts, { pooling: "mean", normalize: true });
  return vectorsFromTensor(tensor, texts.length);
}

export async function embedTexts(
  texts: string[],
  onProgress?: (done: number, total: number) => void
): Promise<number[][]> {
  await initEmbedder();
  const batchSize = 8;
  const output: number[][] = [];
  for (let offset = 0; offset < texts.length; offset += batchSize) {
    const batch = texts.slice(offset, offset + batchSize);
    try {
      output.push(...(await runBatch(batch)));
    } catch (error) {
      if (active?.device !== "webgpu") throw error;
      console.warn("WebGPU inference failed, falling back to WASM INT8", error);
      if (extractor) await extractor.dispose();
      extractor = null;
      active = null;
      pending = null;
      forceWasm = true;
      await initEmbedder(onProgress ? () => onProgress(offset, texts.length) : undefined);
      output.push(...(await runBatch(batch)));
    }
    onProgress?.(Math.min(offset + batch.length, texts.length), texts.length);
  }
  return output;
}
