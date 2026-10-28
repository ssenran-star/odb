import { useEffect, useState } from "react";
import {
  fetchSampleText,
  fetchSamples,
  fetchState,
  postDocuments,
  postRefresh,
  postReset,
  postSearch,
  type SampleFile,
  type SearchHit,
  type SeekdbState,
} from "./api";
import { chunkDocument, titleFromName } from "./chunk";
import { EMBED_DIM, MODEL_ID, embedTexts, getRuntime, initEmbedder } from "./embed";

type Notice = { kind: "ok" | "err"; text: string };

export function App() {
  const [backend, setBackend] = useState("检测推理后端…");
  const [backendKind, setBackendKind] = useState<"loading" | "webgpu" | "wasm">("loading");
  const [modelReady, setModelReady] = useState(false);
  const [state, setState] = useState<SeekdbState | null>(null);
  const [samples, setSamples] = useState<SampleFile[]>([]);
  const [query, setQuery] = useState("DBMS_HYBRID_SEARCH RRF 混合检索");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [fusedIn, setFusedIn] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [pasteTitle, setPasteTitle] = useState("现场笔记");
  const [pasteBody, setPasteBody] = useState("");
  const [embedMs, setEmbedMs] = useState<number | null>(null);

  async function reloadState(): Promise<void> {
    const [nextState, nextSamples] = await Promise.all([fetchState(), fetchSamples()]);
    setState(nextState);
    setSamples(nextSamples.files);
  }

  useEffect(() => {
    let cancelled = false;
    initEmbedder(setBackend)
      .then((runtime) => {
        if (cancelled) return;
        setBackend(runtime.label);
        setBackendKind(runtime.device);
        setModelReady(true);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
        setBackend("模型加载失败");
      });
    const timer = window.setInterval(() => {
      reloadState().catch(() => {
        if (!cancelled) setState(null);
      });
    }, 2000);
    reloadState().catch(() => undefined);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  async function importItems(items: Array<{ source: string; title: string; text: string }>): Promise<void> {
    if (!getRuntime()) throw new Error("本地模型还没准备好");
    const chunks = items.flatMap((item) => chunkDocument(item));
    if (chunks.length === 0) throw new Error("没有可导入的文本");
    const started = performance.now();
    const vectors = await embedTexts(
      chunks.map((chunk) => chunk.document),
      (done, total) => setNotice({ kind: "ok", text: `浏览器向量化 ${done}/${total} · ${getRuntime()?.label ?? ""}` })
    );
    const runtime = getRuntime();
    if (!runtime) throw new Error("本地模型还没准备好");
    const elapsed = Math.round(performance.now() - started);
    setEmbedMs(elapsed);
    const importedAt = new Date().toISOString();
    setNotice({ kind: "ok", text: "写入 seekdb，并刷新索引…" });
    const saved = await postDocuments(
      chunks.map((chunk, index) => ({
        id: chunk.id,
        document: chunk.document,
        embedding: vectors[index],
        metadata: {
          ...chunk.metadata,
          importedAt,
          model: MODEL_ID,
          dtype: runtime.dtype,
          device: runtime.device,
        },
      }))
    );
    await reloadState();
    setNotice({
      kind: "ok",
      text: `写入 ${saved.upserted} 段，集合共 ${saved.count} 段。索引刷新：${saved.refreshNote}`,
    });
  }

  async function importNamed(names: string[]): Promise<void> {
    setBusy(true);
    setNotice(null);
    try {
      const items = [];
      for (const name of names) {
        const text = await fetchSampleText(name);
        items.push({ source: name, title: titleFromName(name), text });
      }
      await importItems(items);
    } catch (error) {
      setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy(false);
    }
  }

  async function onFiles(files: FileList | null): Promise<void> {
    if (!files || files.length === 0) return;
    setBusy(true);
    setNotice(null);
    try {
      const items = [];
      for (const file of Array.from(files)) {
        if (file.size > 200_000) throw new Error(`${file.name} 超过 200KB`);
        items.push({ source: file.name, title: titleFromName(file.name), text: await file.text() });
      }
      await importItems(items);
    } catch (error) {
      setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy(false);
    }
  }

  async function onPaste(): Promise<void> {
    setBusy(true);
    setNotice(null);
    try {
      const source = `${pasteTitle.trim() || "note"}.txt`;
      await importItems([{ source, title: pasteTitle.trim() || "note", text: pasteBody }]);
      setPasteBody("");
    } catch (error) {
      setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy(false);
    }
  }

  async function onSearch(): Promise<void> {
    setBusy(true);
    setNotice(null);
    try {
      if (!getRuntime()) throw new Error("本地模型还没准备好");
      const started = performance.now();
      const [embedding] = await embedTexts([query]);
      const runtime = getRuntime();
      if (!runtime) throw new Error("本地模型还没准备好");
      setEmbedMs(Math.round(performance.now() - started));
      const result = await postSearch({ query, embedding, nResults: 5 });
      setHits(result.hits);
      setFusedIn(result.fusedIn);
      setNotice({
        kind: "ok",
        text: `查询向量 ${EMBED_DIM} 维在浏览器生成（${runtime.label}），排序来自一次 seekdb hybridSearch。`,
      });
      await reloadState();
    } catch (error) {
      setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy(false);
    }
  }

  async function onRefresh(): Promise<void> {
    setBusy(true);
    try {
      const refreshed = await postRefresh();
      await reloadState();
      setNotice({ kind: "ok", text: `索引已刷新 ${refreshed.refreshedAt} · ${refreshed.note}` });
    } catch (error) {
      setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy(false);
    }
  }

  async function onReset(): Promise<void> {
    if (!window.confirm("清空当前 seekdb 集合中的文档？")) return;
    setBusy(true);
    try {
      await postReset();
      setHits(null);
      await reloadState();
      setNotice({ kind: "ok", text: "集合已清空，会话计数已归零。" });
    } catch (error) {
      setNotice({ kind: "err", text: error instanceof Error ? error.message : String(error) });
    } finally {
      setBusy(false);
    }
  }

  const baseSamples = samples.filter((file) => !file.incremental);
  const incrementalSamples = samples.filter((file) => file.incremental);

  return (
    <div className="app">
      <header>
        <div className="brand">
          <div className="seal">端</div>
          <div>
            <h1>星澜文库</h1>
            <p className="sub">浏览器量化向量 · seekdb 混合检索</p>
          </div>
        </div>
        <div className="badge" data-kind={backendKind} data-testid="backend-badge">
          <span className="dot" />
          <span>{backend}</span>
        </div>
      </header>

      <div className="layout">
        <aside className="stack">
          <section className="panel">
            <h2>导入</h2>
            <ul className="file-list">
              {samples.map((file) => (
                <li key={file.name}>
                  <span>{file.name}</span>
                  <span>{file.incremental ? "增量" : "基线"}</span>
                </li>
              ))}
            </ul>
            <div className="actions">
              <button
                className="primary"
                data-testid="import-samples"
                disabled={!modelReady || busy || !state}
                onClick={() => importNamed(baseSamples.map((file) => file.name))}
              >
                导入基线语料
              </button>
              <button
                data-testid="import-incremental"
                disabled={!modelReady || busy || !state}
                onClick={() => importNamed(incrementalSamples.map((file) => file.name))}
              >
                增量导入并刷新
              </button>
            </div>
            <label>
              本地文本
              <input
                type="file"
                accept=".txt,.md,.text,text/plain"
                multiple
                disabled={!modelReady || busy}
                onChange={(event) => {
                  void onFiles(event.target.files);
                  event.target.value = "";
                }}
              />
            </label>
            <input
              type="text"
              value={pasteTitle}
              onChange={(event) => setPasteTitle(event.target.value)}
              aria-label="粘贴文档标题"
            />
            <textarea
              value={pasteBody}
              onChange={(event) => setPasteBody(event.target.value)}
              placeholder="或把一段文字粘贴到这里，向量仍在浏览器里计算。"
              aria-label="粘贴文档正文"
            />
            <button disabled={!modelReady || busy || !pasteBody.trim()} onClick={() => void onPaste()}>
              导入粘贴文本
            </button>
          </section>

          <section className="panel">
            <h2>集合 / 会话</h2>
            {state ? (
              <div className="session" data-testid="session">
                <div>
                  <span>数据库</span>
                  <strong>{state.database}</strong>
                </div>
                <div>
                  <span>集合</span>
                  <strong>{state.collection}</strong>
                </div>
                <div>
                  <span>文档段</span>
                  <strong data-testid="session-count">{state.count}</strong>
                </div>
                <div>
                  <span>向量</span>
                  <strong>
                    {state.dimension} / {state.distance}
                  </strong>
                </div>
                <div>
                  <span>全文</span>
                  <strong>
                    {state.analyzer}/{state.ngramTokenSize}
                  </strong>
                </div>
                <div>
                  <span>服务端嵌入</span>
                  <strong>{state.embeddingFunction === null ? "关闭" : "异常"}</strong>
                </div>
                <div>
                  <span>最近导入</span>
                  <strong>{state.lastImportAt ? state.lastImportAt.slice(11, 19) : "—"}</strong>
                </div>
                <div>
                  <span>索引刷新</span>
                  <strong data-testid="refresh-at">
                    {state.lastRefreshAt ? state.lastRefreshAt.slice(11, 19) : "—"}
                  </strong>
                </div>
              </div>
            ) : (
              <p className="error">seekdb 接口还没连上。确认 npm run dev 已拉起嵌入式引擎。</p>
            )}
            <p className="meta">
              {state?.version || "version pending"}
              {embedMs != null ? ` · 上次浏览器向量化 ${embedMs} ms` : ""}
            </p>
            <div className="actions">
              <button data-testid="refresh-button" disabled={!state || busy} onClick={() => void onRefresh()}>
                刷新索引
              </button>
              <button className="ghost" disabled={!state || busy} onClick={() => void onReset()}>
                清空集合
              </button>
            </div>
          </section>
        </aside>

        <main className="panel">
          <h2>混合检索</h2>
          <div className="search-row">
            <input
              type="search"
              data-testid="search-input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void onSearch();
              }}
              aria-label="查询"
            />
            <button
              className="primary"
              data-testid="search-button"
              disabled={!modelReady || !state || busy || !query.trim()}
              onClick={() => void onSearch()}
            >
              搜索
            </button>
          </div>
          {notice ? <p className={notice.kind === "err" ? "error" : "status"}>{notice.text}</p> : <p className="status" />}
          <div className="results" data-testid="results">
            {hits == null ? (
              <div className="empty">导入语料后搜索。结果顺序就是 seekdb hybridSearch 的返回顺序。</div>
            ) : hits.length === 0 ? (
              <div className="empty">seekdb 没有返回命中。</div>
            ) : (
              hits.map((hit) => (
                <article className="result" key={hit.id}>
                  <header>
                    <h3 data-testid="result-source">{hit.metadata?.source ?? hit.id}</h3>
                    <div className="score">
                      #{hit.rank} · {fusedIn} · {hit.score.toFixed(4)}
                    </div>
                  </header>
                  <p className="snippet">{highlight(hit.document, query)}</p>
                  <div className="meta">
                    {hit.metadata?.title} · chunk {hit.metadata?.chunkIndex ?? 0} · {hit.metadata?.device}/
                    {hit.metadata?.dtype} · {hit.metadata?.model}
                  </div>
                </article>
              ))
            )}
          </div>
        </main>
      </div>
      <footer>
        模型 {MODEL_ID} 由浏览器从 Hugging Face 拉取 ONNX 权重，缓存在本机。查询向量与文档向量都在端侧计算，seekdb 只保存向量、原文和元数据，并用一次 hybridSearch 完成融合。
      </footer>
    </div>
  );
}

function highlight(text: string, query: string) {
  const needles = query
    .split(/\s+/)
    .map((part) => part.trim())
    .filter((part) => part.length >= 2)
    .sort((a, b) => b.length - a.length);
  if (needles.length === 0) return text;
  const pattern = new RegExp(needles.map(escapeRegExp).join("|"), "g");
  const nodes: Array<string | { mark: string }> = [];
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index ?? 0;
    if (start > cursor) nodes.push(text.slice(cursor, start));
    nodes.push({ mark: match[0] });
    cursor = start + match[0].length;
  }
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes.map((node, index) =>
    typeof node === "string" ? <span key={index}>{node}</span> : <mark key={index}>{node.mark}</mark>
  );
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
