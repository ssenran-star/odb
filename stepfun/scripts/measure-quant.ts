/**
 * Local quality note: compare FP32, FP16, and INT8 (q8) MiniLM vectors.
 * This script is not used by the web app. The app embeds in the browser.
 */
import { env, pipeline } from "@huggingface/transformers";

type Extractor = {
  (texts: string[], options?: { pooling?: "mean"; normalize?: boolean }): Promise<{
    data: ArrayLike<number>;
    dispose: () => void;
  }>;
  dispose: () => Promise<void>;
};

const loadFeatureExtractor = pipeline as (
  task: "feature-extraction",
  model: string,
  options?: Record<string, unknown>
) => Promise<Extractor>;

const MODEL = "Xenova/all-MiniLM-L6-v2";
const REVISION = "751bff37182d3f1213fa05d7196b954e230abad9";

const TEXTS = [
  "seekdb 混合检索在数据库内部用 RRF 融合全文和向量。",
  "西湖龙井明前茶芽叶细嫩，干茶扁平光滑。",
  "断桥残雪时桥面积雪先融，远看像桥被截断。",
  "WebGPU runs FP16 weights and WASM falls back to INT8.",
  "增量导入后 refresh_index 让新文档可被检索。",
  "DBMS_HYBRID_SEARCH receives one query_string and one KNN vector.",
];

env.allowLocalModels = false;
env.cacheDir = ".cache/transformers";

async function embed(dtype: "fp32" | "fp16" | "q8"): Promise<number[][]> {
  const extractor = await loadFeatureExtractor("feature-extraction", MODEL, {
    dtype,
    revision: REVISION,
  });
  const started = performance.now();
  const tensor = await extractor(TEXTS, { pooling: "mean", normalize: true });
  const elapsed = performance.now() - started;
  const data = tensor.data as ArrayLike<number>;
  const dim = data.length / TEXTS.length;
  const rows: number[][] = [];
  for (let i = 0; i < TEXTS.length; i += 1) {
    const row = new Array<number>(dim);
    for (let j = 0; j < dim; j += 1) row[j] = Number(data[i * dim + j]);
    rows.push(row);
  }
  tensor.dispose();
  await extractor.dispose();
  console.log(JSON.stringify({ dtype, ms: Math.round(elapsed), dim }));
  return rows;
}

function cosine(a: number[], b: number[]): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / Math.sqrt(na * nb);
}

function top1(rows: number[][], queryIndex: number): number {
  let best = -1;
  let bestScore = -Infinity;
  for (let i = 0; i < rows.length; i += 1) {
    if (i === queryIndex) continue;
    const score = cosine(rows[queryIndex], rows[i]);
    if (score > bestScore) {
      bestScore = score;
      best = i;
    }
  }
  return best;
}

const fp32 = await embed("fp32");
const fp16 = await embed("fp16");
const q8 = await embed("q8");

function report(name: string, rows: number[][]): void {
  const cosines = rows.map((row, index) => cosine(fp32[index], row));
  const mean = cosines.reduce((sum, value) => sum + value, 0) / cosines.length;
  const min = Math.min(...cosines);
  const query = 0;
  console.log(
    JSON.stringify({
      name,
      meanCosineVsFp32: Number(mean.toFixed(6)),
      minCosineVsFp32: Number(min.toFixed(6)),
      fp32Top1: top1(fp32, query),
      quantTop1: top1(rows, query),
    })
  );
}

report("fp16", fp16);
report("q8", q8);
