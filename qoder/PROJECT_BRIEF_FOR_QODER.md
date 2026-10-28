# 交给 Qoder 的任务书

当前作品不是这份任务书里的「备赛知识库」。已经提交的应用是「今天吃什么」，运行、验证和提测以 `README.md`、`RUN.md`、`VERIFY.md`、`SUBMISSION.md` 为准。下面原文只保留作早期脚手架记录。

把下面整段交给 Qoder IDE，让它在本项目里实现「备赛知识库助手」，并发布到 Qoder Sites。

---

请实现「备赛知识库助手」。这是第六届 OceanBase 数据库大赛 Qoder 赛道的作品。代码写在当前项目里，跑通后用 Qoder Sites 发布，访问范围设为任何人可访问，并把公开 URL 写回 `VERIFY.md`。

## 痛点

备赛资料散落在自己的 markdown 笔记、语雀摘录和 README 片段里。只靠文件名或精确关键词，经常找不到那句真正有用的话。需要一个能导入这些文本、按语义和关键词一起搜、并展示原文片段的小应用。

## 必须实现

1. **导入**：读取目录中的 `.md` 与 `.txt`。默认目录是 `data/samples/`。每条记录带上来源路径；长文按标题或空行切成短块，块上保留来源路径和标题。
2. **混合检索**：查询同时走语义向量和关键词全文，在 seekdb 里融合后返回。用户输入一句自然语言或几个关键词都能搜。
3. **展示来源片段**：每条结果给出命中原文、来源文件路径、标题（若有）和相关度。页面上能看出这句话来自哪一篇笔记。

界面保持简单：一个导入入口、一个搜索框、一张结果列表。能在 Qoder Sites 上打开并完成一次搜索即可。

## 技术

- 语言：Python。
- 数据库：seekdb，通过 **pyseekdb** 接入。默认使用嵌入式模式，数据目录由环境变量指定，例如 `pyseekdb.Client(path=SEEKDB_PATH, database=SEEKDB_DATABASE)`。
- 集合：`get_or_create_collection` 创建笔记集合，并配置 embedding function，使写入文档时生成向量。中文全文解析使用 seekdb 的 IK 解析器（`FulltextParserConfig(parser="ik")`）。
- 写入后调用 `collection.refresh_index()`，再检索。
- 检索调用 `collection.hybrid_search`：`query.where_document` 使用 `$contains` 走关键词，`knn.query_texts` 走语义向量，`rank` 使用 `{"rrf": {}}` 融合。返回 `documents`、`metadatas`、`distances`。
- 远程 seekdb 或 OceanBase 只作为可选项。需要时读取 `SEEKDB_HOST`、`SEEKDB_PORT`、`SEEKDB_TENANT`、`SEEKDB_USER`，密码只从环境变量 `SEEKDB_PASSWORD` 读取。仓库里不写真实密钥。

## 验收清单

按语雀赛题的验收口径逐项打勾，并在 `VERIFY.md` 留下可复查的记录：

- [ ] **可运行**：按 `RUN.md` 的步骤能在本地启动，导入 `data/samples/` 后完成一次搜索。
- [ ] **流程里真实使用 seekdb**：导入和搜索都经过 pyseekdb 的 collection，而不是只在内存里过滤文件。`VERIFY.md` 里附上能证明这一点的输出（集合条数、`hybrid_search` 返回的 `distances`、来源 metadata）。
- [ ] **Sites 公开**：站点已在 Qoder Sites 发布，访问范围为任何人可访问。`VERIFY.md` 写入公开 URL，未登录也能打开并复现搜索。
- [ ] **验证样例**：`VERIFY.md` 中的样例可复现。初始数据、输入查询、操作步骤、期望命中和实际结果一致。

## 样例数据

使用仓库里的三篇练习笔记，不要改写它们的「备赛口令」句子，验收依赖这句原文：

- `data/samples/01-hybrid-search.md`
- `data/samples/02-pyseekdb-embedded.md`
- `data/samples/03-contest-prep-rhythm.md`

## 可以后做

用户的复习进度（哪篇看过、哪题要回看）以后可以用 PowerContext 保存。当前验收不要求接入 PowerContext。
