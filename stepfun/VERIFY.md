# 验收走查

环境：Chrome 或 Edge 最新版，已执行 `npm install && npm run dev`，打开 <http://127.0.0.1:5173>。

## 样例

基线语料（「导入基线语料」）：

- `data/samples/01-seekdb-hybrid.txt`
- `data/samples/02-edge-quant.txt`
- `data/samples/03-longjing.txt`
- `data/samples/04-west-lake.txt`

增量语料（第二步再导入）：

- `data/samples/05-incremental-starlan.txt`

## 步骤

1. 右上角徽章变为 `WebGPU · FP16` 或 `WASM · INT8`。本机没有 WebGPU 时必须看到 WASM 降级，而不是停在加载中。
2. 点「导入基线语料」。左侧「文档段」从 0 增加，并出现索引刷新时间。服务端嵌入保持「关闭」。
3. 查询框使用默认查询：

   `DBMS_HYBRID_SEARCH RRF 混合检索`

   点「搜索」。第一条来源应为 `01-seekdb-hybrid.txt`，片段中包含 `DBMS_HYBRID_SEARCH` 与 `Reciprocal Rank Fusion`。龙井、断桥两篇不应排在它前面。
4. 点「增量导入并刷新」。文档段继续增加。
5. 把查询改成：

   `星澜增量文档`

   第一条来源应为 `05-incremental-starlan.txt`。这条文档在步骤 3 时还不在库里。

结果顺序来自一次 `collection.hybridSearch()`，融合发生在 seekdb 的 `DBMS_HYBRID_SEARCH` 里。
