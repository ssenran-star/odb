# 验收样例

一条即可。实现完成后把「实际运行记录」填上，公开站点要能按同样的查询复现。

## 初始数据

导入 `data/samples/` 下三篇练习笔记（应用会按标题或空行切块）：

| 文件 | 内容 |
| --- | --- |
| `data/samples/01-hybrid-search.md` | seekdb 混合检索备赛笔记，含验收口令 |
| `data/samples/02-pyseekdb-embedded.md` | pyseekdb 嵌入式连接备忘 |
| `data/samples/03-contest-prep-rhythm.md` | 初赛节奏与 Sites 发布备忘 |

导入完成后再检索。写入之后需要 `refresh_index()`。

## 输入查询

```text
备赛口令是什么
```

## 操作步骤

1. 按 `RUN.md` 建好虚拟环境，安装 `pyseekdb`，导出嵌入式环境变量。
2. 启动应用，确认日志里的数据目录是 `./data/seekdb`，数据库是 `contest_notes`，集合是 `prep_notes`。
3. 导入 `data/samples/`。
4. 在页面或 CLI 输入上面的查询。
5. 打开 Qoder Sites 上的公开链接，未登录再搜一次同一句话。

## 期望命中

第一条结果来自 `data/samples/01-hybrid-search.md`，片段包含这句原文：

> 备赛口令：湖库一体，写入之后要 refresh_index，再用 hybrid_search。

结果里同时能看到来源路径。另外两篇笔记可以出现在更靠后的位置，但第一条应对上这句口令。

## 如何证明用的是 seekdb

下面三项都要留在「实际运行记录」里，用来说明检索走了 pyseekdb，而不是在内存里扫描文件：

1. 启动日志写出嵌入式 `path`（或远程 host）、`database`、`collection`。
2. 导入后打印 `collection.count()`，数值大于 0，并与切块数量一致。
3. 本次 `hybrid_search` 的返回里带有 `distances`，以及 metadata 中的 `source=data/samples/01-hybrid-search.md`。把这一条结果的原文片段、来源和 distance 贴在下面。

可选补充：对同一集合执行 `collection.get(where={"source": "data/samples/01-hybrid-search.md"})`，能取回含口令的那一块。

## 实际运行记录

实现并发布后填写。提交前这里应换成真实输出和公开 URL。

- 运行时间：
- seekdb 模式与路径：
- `collection.count()`：
- 查询：`备赛口令是什么`
- 命中片段：
- 来源：
- distance：
- Qoder Sites 公开 URL（任何人可访问）：
