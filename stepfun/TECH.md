# 技术说明

## 模型与量化

模型是句子向量 `sentence-transformers/all-MiniLM-L6-v2` 的 ONNX 导出，Hugging Face 仓库 `Xenova/all-MiniLM-L6-v2`，revision `751bff37182d3f1213fa05d7196b954e230abad9`（2025-07-22）。384 维，均值池化后做 L2 归一化，Apache-2.0。浏览器通过 Transformers.js 3 加载，不使用阶跃星辰模型，也不调用任何云端推理 API。

权重体积（Hugging Face LFS，含图结构）：

| 精度 | 文件 | 字节 | 相对 FP32 |
| --- | --- | ---: | ---: |
| FP32 | `onnx/model.onnx` | 90,387,606 | 1× |
| FP16 | `onnx/model_fp16.onnx` | 45,297,825 | 2.00× 压缩 |
| INT8 | `onnx/model_quantized.onnx`（与 `model_int8.onnx` 同一对象） | 22,972,370 | 3.93× 压缩 |

WebGPU 路径使用 FP16。WASM 路径使用 INT8（Transformers.js dtype `q8`）。同一套词表另有约 2MB 级 tokenizer，两种后端共用，不重复计算压缩比。

`npm run measure` 在本机用 ONNX Runtime（CPU）对同一批 6 句做了 FP32 参照。输出维度都是 384。量化发生在权重上，写入 seekdb 的仍是浮点向量。

| 对比 | 与 FP32 的平均余弦 | 最低余弦 | 最近邻是否与 FP32 一致 | 6 句一批耗时 |
| --- | ---: | ---: | --- | ---: |
| FP16 | 0.999999 | 0.999999 | 是 | 34 ms |
| INT8（q8） | 0.986768 | 0.981427 | 是 | 14 ms |
| FP32 参照 | 1 | 1 | — | 17 ms |

FP16 几乎不改变向量。INT8 平均余弦约 0.987，最近邻没有变，体积约为 FP32 的四分之一。上面的耗时是 CPU 上的对照，不是浏览器数字：CPU 上的 FP16 往往更慢，所以浏览器在有 WebGPU 时才走 FP16，WASM 降级走 INT8。

## 端侧运行

推理在浏览器标签页内完成，运行时是 ONNX Runtime Web（由 `@huggingface/transformers` 带入）。

1. 若 `navigator.gpu.requestAdapter()` 成功，加载 FP16 并走 WebGPU。
2. 没有适配器、会话创建失败，或第一次推理抛错，则释放会话，改加载 INT8 并走 WASM。WASM 固定单线程，因此不要求跨域隔离。
3. 右上角徽章只反映真正加载成功的后端：`WebGPU · FP16` 或 `WASM · INT8`。

本机无头 Chrome 没有 WebGPU 适配器（控制台 `No available adapters`），徽章落到 `WASM · INT8`，写入元数据的 dtype 为 `q8`。有适配器的 Chrome / Edge 会先尝试 FP16 WebGPU，推理失败再走同一条降级。

文档切片、文档向量、查询向量都在点击之后于浏览器执行。Node 进程不导入 Transformers，集合的 `embeddingFunction` 设为 `null`。

## seekdb

嵌入模式，配置见 `seekdb.config.json`。seekdb-js 打开 `data/seekdb`，数据库 `kb`，集合 `kb_chunks`。

- 向量索引：HNSW，384 维，余弦距离，无服务端 embedding 函数。
- 全文索引：ngram，`ngram_token_size = 2`，便于中文暗号和英文标识符同时可检索。
- 每段存 `id`、原文、384 维向量，以及 `source / title / chunkIndex / importedAt / model / dtype / device`。
- 会话行在同一库的 `kb_session` 表：集合名、维度、文档数、最近导入时间、最近刷新时间和刷新调用说明。重开进程后从这张表和集合计数恢复。

混合检索只有一次调用：

```ts
collection.hybridSearch({
  query: { whereDocument: { $contains: queryText } },
  knn: { queryEmbeddings: [browserVector] },
  rank: { rrf: {} },
  nResults,
});
```

SDK 把它交给 `DBMS_HYBRID_SEARCH`，在 seekdb 内用 RRF 融合全文和 KNN。应用没有第二次查询，也不在浏览器里合并两路 id。

增量导入走 `collection.upsert`，同一 `source::chunkIndex` 会覆盖。写入后调用 `collection.refresh_index()`（seekdb 1.3+ 内部是 `CALL dbms_index_manager.refresh()`），并再显式执行一次该 `CALL`，然后更新 `kb_session`。新文档在刷新后可被同一次 hybridSearch 命中。

## 状态与取舍

集合维度在打开时核对，不一致就拒绝启动，避免静默换模型。空向量、维度不对、缺原文的请求直接 400/500，防止服务端补算。嵌入式库单进程独占，所以开发命令只起一个 seekdb 进程。

WASM 单线程比多线程慢，但避免了 COOP/COEP 把 Hugging Face 权重下载拦住。WebGPU 优先用 FP16 而不是 4-bit，是为了在满足赛题精度要求的同时让 GPU 路径可用。浏览器每次向量化的毫秒数显示在会话面板。无头 Chrome 在模型已缓存时，完成基线导入、混合检索、增量导入和第二次检索大约 7 秒，两次查询的首条分别是 `01-seekdb-hybrid.txt` 和 `05-incremental-starlan.txt`。
