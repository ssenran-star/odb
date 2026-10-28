# 技术说明

上下文模块 `sddctx` 是一个无状态 CLI。任务材料在 seekdb，任务进度在 PowerContext，代码修改交给 MiniMax。三次运行之间不靠本地 JSON 记住「测过没有」。

## 模块结构

| 路径 | 职责 |
|---|---|
| `sddctx/cli.py` | 入口：`import` / `select` / `test` / `edit` / `state-save` / `resume` / `verify` |
| `sddctx/store.py` | 用 pyseekdb embedded 模式写入、混合检索 |
| `sddctx/context.py` | 只从检索命中里选规格、符号和测试，并拼开发上下文 |
| `sddctx/power.py` | PowerContext HTTP：scope、`/v1/memory/remember`、`/v1/memory/search`、`/v1/context/prepare` |
| `sddctx/minimax_api.py` | `POST /chat/completions` |
| `scripts/run_minimax_edit.py` | 真实修改入口；`--dry-run` 只落盘请求 |
| `sample/` | 班次工资样例。当前 `shiftpay.py` 是 MiniMax 改后的版本；改前快照在 `evidence/snapshots/` |

`verify` 用新的 Python 进程调用 `resume` 和 `select`，用来证明重启后的模块会重新读 PowerContext。

## 上下文怎么选

导入时按文件切块：规格按 `##` 标题，代码和测试按整个文件。每块带上 path、symbol、kind、role，并用本地哈希向量写入 seekdb（不下载嵌入模型）。检索同时做三件事：全库向量查询、按 kind 过滤的向量查询、`where_document.$contains` 加向量的 `hybrid_search`（RRF）。命中之后再用任务里的标识符和中文片段做重叠打分，丢掉零分材料（停车说明因此不会进上下文）。开发上下文中的规格正文、待改符号和测试名都来自这些命中；改完规格并重新 import 后，下一次查询返回新正文。

## 三项技术各自做什么

- **seekdb**：保存工程材料并回答「这次该看哪些规格、文件和测试」。查询日志在 `evidence/seekdb_queries.jsonl`。
- **MiniMax**：`scripts/run_minimax_edit.py` 在设置了 `MINIMAX_API_KEY` 时改 `src/shiftpay.py`。已有一次成功调用：`MINIMAX_BASE_URL=https://api.minimaxi.com/v1`，`MINIMAX_MODEL=MiniMax-M2.5`，功能测试修改前退出码 1、修改后退出码 0。回复与 diff 在 `evidence/minimax_response_summary.json` 和 `records/minimax_development.md`。
- **PowerContext**：记住 `feature_exit`、规格哈希和 nonce。空 scope 的 search/prepare 为空；写入后新进程读到同一条 artifact，并据此选择 `continue_edit` 或 `skip_edit`。
