# 星澜文库

端侧 AI 推理性能优化与 seekdb 混合检索。浏览器在本机把文档和查询变成向量，seekdb 保存原文、向量和元数据，并在引擎内部完成向量 + 全文混合检索。

## 运行（Chrome / Edge）

需要 Node.js 20 或更新版本。仓库里的 `.npmrc` 打开了 `legacy-peer-deps`，因为 `seekdb` 的可选 peer `@seekdb/default-embed` 发布元数据里含有 `workspace:` 协议，npm 默认安装 peer 时会失败。本应用不使用该包，服务端不加载嵌入模型。

```bash
cd stepfun
npm install
npm run dev
```

浏览器打开 <http://127.0.0.1:5173>。

`npm run dev` 会同时做两件事：

1. `npm run seekdb`：用 seekdb-js **嵌入模式**打开本地库，并在 `127.0.0.1:8787` 提供只收向量的 HTTP 接口。
2. Vite 开发服务器，把 `/api` 代理到该接口。

只启动数据库接口：

```bash
npm run seekdb
# 或
bash scripts/start-seekdb.sh
```

嵌入式数据目录、端口和索引参数在 [`seekdb.config.json`](seekdb.config.json)。也可以用环境变量覆盖路径和端口：`SEEKDB_PATH`、`SEEKDB_DATABASE`、`SEEKDB_HOST`、`SEEKDB_PORT`。不要同时开两个进程指向同一个 `SEEKDB_PATH`。

Linux 需要 `libaio`（`sudo apt-get install -y libaio1`；Ubuntu 24 的包名是 `libaio1t64`）。启动脚本会在需要时把 `libaio.so.1t64` 映射成 `libaio.so.1`，并预加载 `libseekdb.so`，避免 `cannot allocate memory in static TLS block`。预加载后 Node 可能打印 `pthread_create: Invalid argument`，只要随后出现 `seekdb embedded api http://127.0.0.1:8787` 就可以继续。首次拉起会下载对应平台的原生包到 `~/.seekdb/bindings/`，嵌入式引擎第一次打开大约需要一分钟。

页面流程：

1. 等右上角徽章变成 `WebGPU · FP16` 或 `WASM · INT8`。没有 WebGPU 时会自动降到 WASM。
2. 点「导入基线语料」。样例在 `data/samples/`，向量在浏览器里计算后再写入 seekdb。
3. 搜索 `DBMS_HYBRID_SEARCH RRF 混合检索`，首条应来自 `01-seekdb-hybrid.txt`。
4. 点「增量导入并刷新」，再搜索 `星澜增量文档`，应命中 `05-incremental-starlan.txt`。

也可以从本机选择 `.txt` / `.md`，或把文字粘贴进左侧输入框。服务端没有 embedding 函数，缺向量的请求会被拒绝。

## 模型从哪里来

权重不进仓库。第一次向量化时，Transformers.js 从 Hugging Face 仓库 `Xenova/all-MiniLM-L6-v2`（revision `751bff37182d3f1213fa05d7196b954e230abad9`）下载 ONNX：

- WebGPU：`onnx/model_fp16.onnx`
- WASM 降级：`onnx/model_quantized.onnx`（INT8 / q8）

另外会下载 `tokenizer.json`、`tokenizer_config.json` 和 `config.json`。文件进浏览器缓存，不需要 API key，也没有云端推理。可选的体积/质量测量脚本会把权重缓存在 `stepfun/.cache/`（已 gitignore）：

```bash
npm run measure
```

## 可选自检

`npm run smoke` 用调用方提供的合成向量检查嵌入式 seekdb 的 hybridSearch 和增量刷新。它不是应用的推理路径。

技术说明见 [TECH.md](TECH.md)，验收步骤见 [VERIFY.md](VERIFY.md)。
